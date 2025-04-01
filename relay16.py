# This is for a Sainsmart USB 16-channel relay
# SKU: http://wiki.sainsmart.com/index.php/101-70-208
# The wiki link gives serial commands
# SKU: 101-70-208
#
# QinHeng Electronics HL-340 USB-Serial adapter
#
# To run with pyusb debugging:
#
#   PYUSB_DEBUG=debug python relay.py
#
# Grab the vendor and product codes from syslog when plugging in the relay:
#
#  Ex:  idVendor=1a86, idProduct=7523
#
# Adapted from ldnelso2 https://github.com/ldnelso2/sainsmart/blob/master/relay.py
# Adapted from RJ's gitgist https://gist.github.com/RJ/7acba5b06a03c9b521601e08d0327d56
# ... and pyusb tutorial:  https://github.com/pyusb/pyusb

import time
import traceback

import usb.core
import usb.util
import logging
from utils import get_device_id

class SainSmartHid:
    command = {
        'Status': [58, 70, 69, 48, 49, 48, 48, 48, 48, 48, 48, 49, 48, 70, 49, 13, 10],
        'Status-Return': [58, 70, 69, 48, 49, 48, 48, 50, 48, 48, 48, 48, 48, 70, 70, 13, 10],
        '1 ON': [58, 70, 69, 48, 53, 48, 48, 48, 48, 70, 70, 48, 48, 70, 69, 13, 10],
        '1 OFF': [58, 70, 69, 48, 53, 48, 48, 48, 48, 48, 48, 48, 48, 70, 68, 13, 10],
        '2 ON': [58, 70, 69, 48, 53, 48, 48, 48, 49, 70, 70, 48, 48, 70, 68, 13, 10],
        '2 OFF': [58, 70, 69, 48, 53, 48, 48, 48, 49, 48, 48, 48, 48, 70, 67, 13, 10],
        '3 ON': [58, 70, 69, 48, 53, 48, 48, 48, 50, 70, 70, 48, 48, 70, 67, 13, 10],
        '3 OFF': [58, 70, 69, 48, 53, 48, 48, 48, 50, 48, 48, 48, 48, 70, 66, 13, 10],
        '4 ON': [58, 70, 69, 48, 53, 48, 48, 48, 51, 70, 70, 48, 48, 70, 66, 13, 10],
        '4 OFF': [58, 70, 69, 48, 53, 48, 48, 48, 51, 48, 48, 48, 48, 70, 65, 13, 10],
        '5 ON': [58, 70, 69, 48, 53, 48, 48, 48, 52, 70, 70, 48, 48, 70, 65, 13, 10],
        '5 OFF': [58, 70, 69, 48, 53, 48, 48, 48, 52, 48, 48, 48, 48, 70, 57, 13, 10],
        '6 ON': [58, 70, 69, 48, 53, 48, 48, 48, 53, 70, 70, 48, 48, 70, 57, 13, 10],
        '6 OFF': [58, 70, 69, 48, 53, 48, 48, 48, 53, 48, 48, 48, 48, 70, 56, 13, 10],
        '7 ON': [58, 70, 69, 48, 53, 48, 48, 48, 54, 70, 70, 48, 48, 70, 56, 13, 10],
        '7 OFF': [58, 70, 69, 48, 53, 48, 48, 48, 54, 48, 48, 48, 48, 70, 55, 13, 10],
        '8 ON': [58, 70, 69, 48, 53, 48, 48, 48, 55, 70, 70, 48, 48, 70, 55, 13, 10],
        '8 OFF': [58, 70, 69, 48, 53, 48, 48, 48, 55, 48, 48, 48, 48, 70, 54, 13, 10],
        '9 ON': [58, 70, 69, 48, 53, 48, 48, 48, 56, 70, 70, 48, 48, 70, 54, 13, 10],
        '9 OFF': [58, 70, 69, 48, 53, 48, 48, 48, 56, 48, 48, 48, 48, 70, 53, 13, 10],
        '10 ON': [58, 70, 69, 48, 53, 48, 48, 48, 57, 70, 70, 48, 48, 70, 53, 13, 10],
        '10 OFF': [58, 70, 69, 48, 53, 48, 48, 48, 57, 48, 48, 48, 48, 70, 52, 13, 10],
        '11 ON': [58, 70, 69, 48, 53, 48, 48, 48, 65, 70, 70, 48, 48, 70, 52, 13, 10],
        '11 OFF': [58, 70, 69, 48, 53, 48, 48, 48, 65, 48, 48, 48, 48, 70, 51, 13, 10],
        '12 ON': [58, 70, 69, 48, 53, 48, 48, 48, 66, 70, 70, 48, 48, 70, 51, 13, 10],
        '12 OFF': [58, 70, 69, 48, 53, 48, 48, 48, 66, 48, 48, 48, 48, 70, 50, 13, 10],
        '13 ON': [58, 70, 69, 48, 53, 48, 48, 48, 67, 70, 70, 48, 48, 70, 50, 13, 10],
        '13 OFF': [58, 70, 69, 48, 53, 48, 48, 48, 67, 48, 48, 48, 48, 70, 49, 13, 10],
        '14 ON': [58, 70, 69, 48, 53, 48, 48, 48, 68, 70, 70, 48, 48, 70, 49, 13, 10],
        '14 OFF': [58, 70, 69, 48, 53, 48, 48, 48, 68, 48, 48, 48, 48, 70, 48, 13, 10],
        '15 ON': [58, 70, 69, 48, 53, 48, 48, 48, 69, 70, 70, 48, 48, 70, 48, 13, 10],
        '15 OFF': [58, 70, 69, 48, 53, 48, 48, 48, 69, 48, 48, 48, 48, 70, 70, 13, 10],
        '16 ON': [58, 70, 69, 48, 53, 48, 48, 48, 70, 70, 70, 48, 48, 70, 70, 13, 10],
        '16 OFF': [58, 70, 69, 48, 53, 48, 48, 48, 70, 48, 48, 48, 48, 70, 69, 13, 10],
        'ALL ON': [58, 70, 69, 48, 70, 48, 48, 48, 48, 48, 48, 49, 48, 48, 50, 70, 70, 70, 70, 69, 51, 13, 10],
        'ALL OFF': [58, 70, 69, 48, 70, 48, 48, 48, 48, 48, 48, 49, 48, 48, 50, 48, 48, 48, 48, 69, 49, 13, 10],

        'all_on': [0x3A, 0x46, 0x45, 0x30, 0x46, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x31, 0x30, 0x30, 0x32, 0x30, 0x30,
                   0x30, 0x30, 0x45, 0x31, 0x0D, 0x0A],

        'all_off': [0x3A, 0x46, 0x45, 0x30, 0x46, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x31, 0x30, 0x30, 0x32, 0x46,
                    0x46,
                    0x46, 0x46, 0x45, 0x33, 0x0D, 0x0A]
    }

    command_indexes = [
        {True: 'ALL ON', False: 'ALL OFF'},
        {True: '1 ON', False: '1 OFF'},
        {True: '2 ON', False: '2 OFF'},
        {True: '3 ON', False: '3 OFF'},
        {True: '4 ON', False: '4 OFF'},
        {True: '5 ON', False: '5 OFF'},
        {True: '6 ON', False: '6 OFF'},
        {True: '7 ON', False: '7 OFF'},
        {True: '8 ON', False: '8 OFF'},
        {True: '9 ON', False: '9 OFF'},
        {True: '10 ON', False: '10 OFF'},
        {True: '11 ON', False: '11 OFF'},
        {True: '12 ON', False: '12 OFF'},
        {True: '13 ON', False: '13 OFF'},
        {True: '14 ON', False: '14 OFF'},
        {True: '15 ON', False: '15 OFF'},
        {True: '16 ON', False: '16 OFF'},
    ]

    def __init__(self,
                 channel_attached_external_handler=None,
                 output_changed_external_handler=None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info('Starting')
        self.device = None
        self.ep = None
        self.channel_attached_external_handler = channel_attached_external_handler
        self.output_changed_external_handler = output_changed_external_handler
        self.sn = get_device_id()
        self.connect_device()
        # Publish available channels
        self.publish_available_channels()

    def publish_available_channels(self):
        """Publish all available relay channels for discovery by Home Assistant"""
        if self.channel_attached_external_handler:
            for i in range(1, 17):
                self.channel_attached_external_handler(self.sn, i, 'Output')

    def disconnect_device(self):
        try:
            if self.device:
                self.logger.info('Disconnecting device')
                usb.util.dispose_resources(self.device)
        except Exception:
            self.logger.exception('Failure disconnecting')

    def connect_device(self):
        self.disconnect_device()

        try:
            self.logger.info('Connecting device')

            self.device = usb.core.find(idVendor=0x1a86, idProduct=0x7523, find_all=False)   # Find first matching device
            if self.device is None:
                self.logger.error('SainSmart device not found')
                raise NotImplementedError('SainSmart device not found')
            self.logger.info("Device: %s" % self.device)

            if self.device.is_kernel_driver_active(0):
                self.logger.info('detach_kernel_driver')
                self.device.detach_kernel_driver(0)

            # 2020/08/30
            try:
                cfg = self.device.get_active_configuration()
            except usb.core.USBError:
                cfg = None
            if cfg is None:
                self.logger.info('Configuration == None, resetting')
                self.device.set_configuration()

            intf = cfg[(0, 0)]

            self.ep = usb.util.find_descriptor(
                intf,
                # match the first OUT endpoint
                custom_match=lambda e: \
                    usb.util.endpoint_direction(e.bEndpointAddress) == \
                    usb.util.ENDPOINT_OUT)

            assert self.ep is not None

            # Since I'm using this to send a signal to a gate controller, I'm simulating just
            # pressing a button to make the circuit for 2 seconds, then releasing:
            # Example:
            # close_relay_cmd = [0xA0, 0x01, 0x01, 0xA2]
            # open_relay_cmd = [0xA0, 0x01, 0x00, 0xA1]
            # self.ep.write(close_relay_cmd)
            # time.sleep(1)
            # self.ep.write(open_relay_cmd)

            # Sainsmart 16-channel commands
            # NOTE - it looks like the sainsmart likes to receive the commands
            # for some reason as a tuple or a list from python.
            # dev.reset() reset

            # TODO: dev.reset() resets the driver
            # TODO: Should make a function to reset and re-run the init of USB control

            ######### Overall Sainsmart Control Commands List Array ###############
            # Decimal format, converted from hex based on sainsmart documentation
            # The format for indexing the control serial messages is:
            # Relay Number X 2 = turn on that relay
            # Relay Number X 2 + 1 = turn off that relay
        except Exception as e:
            self.logger.exception('Failure connecting')
            raise RuntimeError('SainSmart init failed')

    def set_output_state(self, sn, index, state, force_notify=False):

        # Write command to device with optional retry logic.
        def write_command_to_device(retry=True):
            try:
                self.ep.write(command)
                self.logger.debug(f'Writing command: {command}')
                return True
            except Exception as e:
                # Logger.exception already includes the traceback
                self.logger.exception(f'Failed writing to device {"(will retry)" if retry else "(gave up)"}')
                if retry:
                    self.connect_device()
                    return write_command_to_device(retry=False)
                return False
        try:
            if not sn == self.sn: # Ignore if the serial number doesn't match
                self.logger.debug(f'not my sn: {sn} vs {self.sn}')
                return
            command = self.command[self.command_indexes[index][state]]
        except Exception as e:
            self.logger.exception('Failed obtaining command for index: {}, state {}'.format(index, state))
            return
        if write_command_to_device() and self.output_changed_external_handler:
            # Use "kitchen" as the channel name for relay outputs
            self.output_changed_external_handler(self.sn, index, state)

    def test_allonoff(self):
        time.sleep(10)
        # self.ep.write(self.command['all_off'])
        # time.sleep(1)
        # self.ep.write(self.command['all_on'])
        # time.sleep(5)
        # self.ep.write(self.command['all_off'])
        # time.sleep(1)
        self.ep.write(self.command['1 ON'])
        time.sleep(1)
        self.ep.write(self.command['2 ON'])
        time.sleep(1)
        self.ep.write(self.command['3 ON'])
        time.sleep(1)
        self.ep.write(self.command['4 ON'])
        time.sleep(1)
        self.ep.write(self.command['5 ON'])
        time.sleep(1)
        self.ep.write(self.command['6 ON'])
        time.sleep(1)
        self.ep.write(self.command['7 ON'])
        time.sleep(1)
        self.ep.write(self.command['8 ON'])
        time.sleep(1)
        self.ep.write(self.command['9 ON'])
        time.sleep(1)
        self.ep.write(self.command['10 ON'])
        time.sleep(1)
        self.ep.write(self.command['11 ON'])
        time.sleep(1)
        self.ep.write(self.command['12 ON'])
        time.sleep(1)
        self.ep.write(self.command['13 ON'])
        time.sleep(1)
        self.ep.write(self.command['14 ON'])
        time.sleep(1)
        self.ep.write(self.command['15 ON'])
        time.sleep(1)
        self.ep.write(self.command['16 ON'])
        time.sleep(5)

        self.ep.write(self.command['1 OFF'])
        time.sleep(1)
        self.ep.write(self.command['2 OFF'])
        time.sleep(1)
        self.ep.write(self.command['3 OFF'])
        time.sleep(1)
        self.ep.write(self.command['4 OFF'])
        time.sleep(1)
        self.ep.write(self.command['5 OFF'])
        time.sleep(1)
        self.ep.write(self.command['6 OFF'])
        time.sleep(1)
        self.ep.write(self.command['7 OFF'])
        time.sleep(1)
        self.ep.write(self.command['8 OFF'])
        time.sleep(1)
        self.ep.write(self.command['9 OFF'])
        time.sleep(1)
        self.ep.write(self.command['10 OFF'])
        time.sleep(1)
        self.ep.write(self.command['11 OFF'])
        time.sleep(1)
        self.ep.write(self.command['12 OFF'])
        time.sleep(1)
        self.ep.write(self.command['13 OFF'])
        time.sleep(1)
        self.ep.write(self.command['14 OFF'])
        time.sleep(1)
        self.ep.write(self.command['15 OFF'])
        time.sleep(1)
        self.ep.write(self.command['16 OFF'])

    def test_1by1(self):
        time.sleep(10)
        # self.ep.write(self.command['all_off'])
        # time.sleep(1)
        # self.ep.write(self.command['all_on'])
        # time.sleep(5)
        # self.ep.write(self.command['all_off'])
        # time.sleep(1)
        self.ep.write(self.command['1 ON'])
        time.sleep(1)
        self.ep.write(self.command['1 OFF'])
        time.sleep(1)
        self.ep.write(self.command['2 ON'])
        time.sleep(1)
        self.ep.write(self.command['2 OFF'])
        time.sleep(1)
        self.ep.write(self.command['3 ON'])
        time.sleep(1)
        self.ep.write(self.command['3 OFF'])
        time.sleep(1)
        self.ep.write(self.command['4 ON'])
        time.sleep(1)
        self.ep.write(self.command['4 OFF'])
        time.sleep(1)
        self.ep.write(self.command['5 ON'])
        time.sleep(1)
        self.ep.write(self.command['5 OFF'])
        time.sleep(1)
        self.ep.write(self.command['6 ON'])
        time.sleep(1)
        self.ep.write(self.command['6 OFF'])
        time.sleep(1)
        self.ep.write(self.command['7 ON'])
        time.sleep(1)
        self.ep.write(self.command['7 OFF'])
        time.sleep(1)
        self.ep.write(self.command['8 ON'])
        time.sleep(1)
        self.ep.write(self.command['8 OFF'])
        time.sleep(1)
        self.ep.write(self.command['9 ON'])
        time.sleep(1)
        self.ep.write(self.command['9 OFF'])
        time.sleep(1)
        self.ep.write(self.command['10 ON'])
        time.sleep(1)
        self.ep.write(self.command['10 OFF'])
        time.sleep(1)
        self.ep.write(self.command['11 ON'])
        time.sleep(1)
        self.ep.write(self.command['11 OFF'])
        time.sleep(1)
        self.ep.write(self.command['12 ON'])
        time.sleep(1)
        self.ep.write(self.command['12 OFF'])
        time.sleep(1)
        self.ep.write(self.command['13 ON'])
        time.sleep(1)
        self.ep.write(self.command['13 OFF'])
        time.sleep(1)
        self.ep.write(self.command['14 ON'])
        time.sleep(1)
        self.ep.write(self.command['14 OFF'])
        time.sleep(1)
        self.ep.write(self.command['15 ON'])
        time.sleep(1)
        self.ep.write(self.command['15 OFF'])
        time.sleep(1)
        self.ep.write(self.command['16 ON'])
        time.sleep(1)
        self.ep.write(self.command['16 OFF'])
        time.sleep(1)


def main():
    relay = SainSmartHid()
    #relay.set_output_state(1, True, 'abc')
    #time.sleep(5)
    #relay.set_output_state(1, False, 'def')
    relay.test_1by1()


if __name__ == "__main__":
    main()
