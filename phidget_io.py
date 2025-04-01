#!/usr/bin/env python
import importlib
import shelve
import traceback
import logging

from Phidget22.ChannelClass import ChannelClass
# from Phidget22.Devices.DigitalInput import DigitalInput            Loaded dynamically
# from Phidget22.Devices.DigitalOutput import DigitalOutput          Loaded dynamically
from Phidget22.Devices.Manager import Manager
from Phidget22.ErrorCode import ErrorCode
from Phidget22.PhidgetException import PhidgetException
from channel_states import ChannelStates


# Manages all Phidgets
# Should really be a singleton


class PhidgetsManager:
    manager22 = None
    channels = {}
    default_output_state = ChannelStates()
    output_states = ChannelStates()             # Needed to be able to set outputs on init to previous state
    input_changed_external_handler = None
    output_changed_external_handler = None
    INPUT = 'Input'
    OUTPUT = 'Output'
    OUTPUTS_STATES_DB = 'phidgets_outputs'
    STATES = 'states'
    DEFAULTS = 'defaults'

    # Initialization
    def __init__(self, channel_attached_external_handler=None,
                 channel_detached_external_handler=None,
                 input_changed_external_handler=None,
                 output_changed_external_handler=None):
        try:
            self.logger = logging.getLogger(self.__class__.__name__)
            self.logger.info('Starting')
            self.channel_attached_handler = channel_attached_external_handler
            self.channel_detached_handler = channel_detached_external_handler
            self.input_changed_external_handler = input_changed_external_handler
            self.output_changed_external_handler = output_changed_external_handler
            self.read_output_states()
            self.manager22 = Manager()
            self.manager22.setOnAttachHandler(self.on_manager_attach_handler)
            self.manager22.setOnDetachHandler(self.on_manager_detach_handler)
            self.manager22.open()
        except Exception as e:
            traceback.print_tb(e.__traceback__)
            self.logger.exception('init')
            raise e

    # def get_device_serials(self):
    #     """Returns a list of serial numbers for all connected Phidget devices"""
    #     return list(self.channels.keys())  # Assuming self.channels is a dict keyed by serial numbers

    def write_output_states(self):
        try:
            self.logger.debug('Writing outputs states')
            states = {self.STATES: self.output_states, self.DEFAULTS: self.default_output_state}
            with shelve.open(self.OUTPUTS_STATES_DB) as db:
                db.update(states)
            #self.logger.debug('Saved output states: %s', states)       # This is a long log line
        except Exception as e:
            self.logger.exception('Failed writing to db')

    def read_output_states(self):
        try:
            self.logger.info('Loading output states')
            with shelve.open(self.OUTPUTS_STATES_DB) as db:
                states = dict(db)
                self.logger.debug('Loaded outputs states: %s', states)
            if self.STATES in states:
                self.output_states = states[self.STATES]
            if self.DEFAULTS in states:
                self.default_output_state = states[self.DEFAULTS]
        except Exception as e:
            self.logger.exception('Failed reading from db')

    # was never called...
    #def __del__(self):
        #logger.exception('************************** dying **************************')

    def close(self):
        # Strange things will happen in the next run if the phidget objects aren't close
        if self.manager22:
            self.manager22.close()
            for ch in self.channels.values():
                ch.close()
        self.logger.info('Closed all phidget objects')

    def display_error(self, e):
        if e.code == ErrorCode.EPHIDGET_WRONGDEVICE:
            self.logger.error("Desc: %s: Commonly occurs when the Phidget function called does not match the class of the channel that called it.", e.details)
        elif e.code == ErrorCode.EPHIDGET_NOTATTACHED:
            self.logger.error("Desc: %s: Occurs when Phidget functions are called before the channel has been opened and attached.", e.details)
        elif e.code == ErrorCode.EPHIDGET_NOTCONFIGURED:
            self.logger.error("Desc: %s: Commonly occurs when Enable-type functions are called before all Must-Set Parameters have been set for the channel.\n"
                         "\tCheck the API page to see which parameters are labeled \"Must be Set\" on the right-hand side of the list.", e.details)
        elif e.code == ErrorCode.EPHIDGET_UNKNOWNVAL:
            self.logger.error("Desc: %s", e.details)
        else:
            self.logger.error("Phidget Error: %s %s", e.details, ErrorCode.getName(e.code))

    def on_manager_attach_handler(self, manager, ch_readonly):
        print('on_manager_attach_handler')
        """
        Fired when a Phidget channel is identified by the manager
        NOTE: ch is read-only!!!
        :param manager: The Phidget manager that fired the attach event
        :param ch_readonly: The READ-ONLY Phidget channel that fired the attach event
        """
        try:
            details = ''
            sn = ch_readonly.getDeviceSerialNumber()
            index = ch_readonly.getChannel()
            klass = ch_readonly.getChannelClassName()
            details = '%s %i/%i' % (klass, sn, index)

            # Dynamically create a phidget channel
            if klass.startswith('Phidget'):  # PhidgetDigitalInput
                python_klass_name = klass.split('Phidget')[1]
            else:
                self.logger.error('ERROR: Unknown classname: %s' % klass)
                return
            details = '%s %i/%i' % (python_klass_name, sn, index)
            # Dynamically create phidget channel class
            ch_new = getattr(importlib.import_module('Phidget22.Devices.' + python_klass_name), python_klass_name)()

            try:
                ch_new.setOnStateChangeHandler(self.on_state_change_handler)
            except:
                pass  # if it fails, the it must not support state-change events
            self.logger.debug("Manager attach event: %s %i/%i" % (python_klass_name, sn, index))

            ch_new.setOnAttachHandler(self.on_channel_attach_handler)
            ch_new.setOnDetachHandler(self.on_channel_detach_handler)
            ch_new.setOnErrorHandler(self.on_error_handler)
            #ch_new.setOnPropertyChangeHandler(self.on_property_change_handler)

            ch_new.setDeviceSerialNumber(sn)
            ch_new.setChannel(index)
            #ch_new.open()
            # every so often, on_channel_attach_handler throws an exception on getDeviceSerialNumber(). calling openWaitForAttachment seems to fix it
            ch_new.openWaitForAttachment(10000)

            # every so often, on_channel_attach_handler throws an exception on getDeviceSerialNumber()
            # this seems to fix it...
            #while not ch_new.getAttached():
            #    self.logger.debug("Waiting for Attached: %s %i/%i" % (python_klass_name, sn, index))
            #    time.sleep(0.01)
            self.logger.debug("Attached: %s %i/%i" % (python_klass_name, sn, index))

        except PhidgetException as e:
            self.logger.exception(f'**************Error in Manager Attach Event: {details}')
            self.display_error(e)

    def on_channel_attach_handler(self, ch):
        """
        Fired when a Phidget channel attaches and is available
        :param ch: The Phidget channel that fired the attach event
        """
        try:
            sn = ch.getDeviceSerialNumber()
            index = ch.getChannel()

            # getChannelClassName fails before channel is attached - will be fixed in phidget release after Jan/2019: https://www.phidgets.com/phorum/viewtopic.php?f=26&t=9199&p=29646#p29646
            if ch.getChannelClass() == ChannelClass.PHIDCHCLASS_DIGITALINPUT:
                ch.type = self.INPUT
            elif ch.getChannelClass() == ChannelClass.PHIDCHCLASS_DIGITALOUTPUT:
                ch.type = self.OUTPUT
            else:
                self.logger.warning('Attached unknown type %s %i/%i)' % (ch.getChannelClassName(), sn, index))
            self.logger.info('Channel attach event: %s %i/%i' % (ch.type, sn, index))

            #if self.get_channel_id(ch.type, sn, index) not in self.channels:
            self.channels[self.get_channel_id_from_ch(ch)] = ch

            if ch.type == self.OUTPUT:
                initial_state = self.get_initial_output_state(sn, index)
                self.logger.debug(f'Setting initial value: {initial_state}')
                # Force set_state to call notify_state_change even if state was not changed
                self.set_output_state(ch, initial_state, force_notify=True)

                # Force notification of initial state
                current_state = ch.getState()
                self.notify_state_change(ch, current_state)

            # Notify external handler
            if self.channel_attached_handler:
                self.channel_attached_handler(sn, index, ch.type)

        except PhidgetException as e:
            self.logger.exception('**************Error in Channel Attach Event*********************')
            self.display_error(e)

    def on_manager_detach_handler(self, manager, ch_readonly):
        print('on_manager_detach_handler')
        """
        Fired when a Phidget channel is detached by the manager
        NOTE: ch is read-only!!!
        :param manager: The Phidget manager that fired the attach event
        :param ch_readonly: The READ-ONLY Phidget channel that fired the attach event
        """
        self.logger.warning('Manager detach event: %s %d/%d' % (ch_readonly.getChannelClassName(), ch_readonly.getDeviceSerialNumber(), ch_readonly.getChannel()))

    def on_channel_detach_handler(self, ch):
        print('on_channel_detach_handler')
        """
        Fired when a Phidget channel detaches
        :param ch: The Phidget channel that fired the attach event
        """

        try:
            self.logger.warning("Detach event: %s %d/%d" % (ch.type, ch.getDeviceSerialNumber(), ch.getChannel()))
            self.channels.pop(self.get_channel_id_from_ch(ch), None)

            # Notify external handler
            if self.channel_detached_handler:
                sn = ch.getDeviceSerialNumber()
                index = ch.getChannel()
                self.channel_detached_handler(sn, index, ch.type)

        except PhidgetException as e:
            self.logger.exception('Error in Detach Event')
            self.display_error(e)

    def on_error_handler(self, ch, errorCode, errorString):
        print('on_error_handler')
        """
        Fired when a Phidget channel with onErrorHandler registered encounters an error in the library
        :param ch: the Phidget channel that fired the attach event
        :param errorCode: the code associated with the error of enum type ph.ErrorEventCode
        :param errorString: string containing the description of the error fired
        """
        self.logger.error("Phidget Error Event: %s (%s)" % (errorString, errorCode))
        try:
            self.logger.error("Phidget Error Event on %s %d/%d: %s (%s)" % (ch.type, ch.getDeviceSerialNumber(), ch.getChannel(), errorString, errorCode))
        except Exception as e:
            pass

    def on_property_change_handler(self, ch, propertyName):
        print('on_property_change_handler')
        """
        Occurs when a property is changed externally from the user channel, usually from a network client attached to the same channel.
        :param ch:
        :param propertyName:
        """
        self.logger.info("Property event: Channel Class: %s %d/%d, state: %s" % (ch.type, ch.getDeviceSerialNumber(), ch.getChannel(), propertyName))

    def on_state_change_handler(self, ch, state):
        """
        Fired when a DigitalInput channel detects a state change
        :param ch: The DigitalInput channel that fired the StateChange event
        :param state: The reported state from the DigitalInput channel
        """
        self.logger.info("State event: Channel Class: %s %d/%d, state: %r" % (ch.type, ch.getDeviceSerialNumber(), ch.getChannel(), state))
        self.notify_state_change(ch, state)

    def set_saved_output_state(self, ch, state):
        sn = str(ch.getDeviceSerialNumber())
        if sn not in self.output_states:
            self.output_states[sn] = {}
        self.output_states[sn][str(ch.getChannel())] = state
        self.write_output_states()

    def get_channel_id_from_ch(self, ch):
        return self.get_channel_id(ch.type, ch.getDeviceSerialNumber(), ch.getChannel())

    def get_channel_id(self, classname, sn, index):
        return classname + "_" + str(sn) + "_" + str(index)

    def get_channel(self, classname, sn, index):
        ch_id = self.get_channel_id(classname, sn, index)
        if ch_id in self.channels:
            return self.channels[ch_id]
        else:
            self.logger.warning('Channel %s %s/%s not found in channels{}', classname, sn, index)

    def notify_state_change(self, ch, state):
        sn = ch.getDeviceSerialNumber()
        index = ch.getChannel()

        self.logger.info("Notifying %s %i/%i state changed to: %r" % (ch.type, sn, index, state))
        if ch.type == self.INPUT:
            if self.input_changed_external_handler:
                self.input_changed_external_handler(sn, index, state)
        elif ch.type == self.OUTPUT:
            if self.output_changed_external_handler:
                self.output_changed_external_handler(sn, index, state)
        else:
            self.logger.error("Notifying State Change: %i/%i unknown channel type: %s" % (sn, index, ch.type))

    def set_output_state_from_sn_index(self, sn, index, state):
        ch = self.get_channel(self.OUTPUT, sn, index)
        if ch is None:
            self.logger.warning('Failed to find output %s/%s' % (sn, index))
            return False
        return self.set_output_state(ch, state)

    def set_output_state(self, ch, state, force_notify=False):
        """
        Sets channel to supplied state.
        :param ch:
        :param state:
        :param force_notify: Will call notify_state_change even if state did not change
        :return: Returns True if state was changed, False current state == supplied state
        """
        state = bool(state)
        self.logger.info(f'Request to change state: {ch.getDeviceSerialNumber()}/{ch.getChannel()} from {ch.getState()}--> {state} ({force_notify})')
        state_changed = False
        if state is None:
            # state can be None from on_channel_attach_handler, which means we just want to send the notification of the current state
            if force_notify:
                state = ch.getState()
            else:
                return False
        elif ch and ch.getState() != state:
            ch.setState(int(state))
            state_changed = True
            # TODO: consider using setState_async

        # TODO: Consider sending event even if state not changed, to resolve sync issues
        # PhidgetManager library only calls state change handler for Inputs.
        if state_changed or force_notify:
            self.logger.info(f'Setting state: {ch.getDeviceSerialNumber()}/{ch.getChannel()} --> {state}')
            self.notify_state_change(ch, state)
            self.output_states.set_state(ch.getDeviceSerialNumber(), ch.getChannel(), state is True)
            self.write_output_states()
        return state_changed

    def set_default_output_states(self, sn, states):
        """
        Sets the initial states of the outputs, for the next time that the phidget connects
        :param sn:
        :param initial_outputs: string-based bitmask of the states
        :return: None
        """
        self.logger.info("Settings states for Phidget #%s, '%s'" % (sn, states))
        self.default_output_state.del_sn(sn)  # Clear the states for this sn
        for i in range(0, len(states)):
            state = 1 if states[i] in [1, '1'] else 0 if states[i] in [0, '0'] else '*' if states[i] in ['*'] else None
            self.default_output_state.set_state(sn, i, state)
            if state in [1, 0]:
                self.logger.info("Setting Phidget #%s/%i, state: %s" % (sn, i, states[i]))
                self.set_output_state_from_sn_index(sn, i, state)
        self.write_output_states()

    def get_initial_output_state(self, sn, index):
        try:
            default_state_type = self.default_output_state.get_state(sn, index)
            if default_state_type == 1:
                return True
            elif default_state_type == 0:
                return False
            else:       # empty default type means to use last state
                return self.output_states.get_state(sn, index)
        except Exception:
            return None

    def get_states(self):
        for ch in self.channels.values():
            self.notify_state_change(ch, ch.getState())


def main():
    import settings
    import logging.config

    logging.config.dictConfig(settings.LOGGING)
    gpios = PhidgetsManager(None, None)
    import time
    logger = logging.getLogger('YOYO')
    logger.info('Eh!')

    try:
        time.sleep(4)
        while True:
            gpios.set_output_state_from_sn_index(344662, 0, True)
            time.sleep(1)
            gpios.set_output_state_from_sn_index(344662, 0, False)
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    print('ready')


if __name__ == "__main__":
    main()
