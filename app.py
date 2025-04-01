# app.py
import logging
import os
from ha_mqtt import HAMQTTClient

from phidget_io import PhidgetsManager
from gpio import GpiosManager
from relay16 import SainSmartHid



class PhidgetApp:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.phidgets = None
        self.relay = None
        self.gpios = None

        # Initialize MQTT client
        self.ha_mqtt = HAMQTTClient(
            os.environ.get('MQTT_BROKER', 'BROKER_IP'),
            os.environ.get('MQTT_PORT', 1883),
            os.environ.get('MQTT_USER', 'BROKER_USERNMAE'),
            os.environ.get('MQTT_PASSWORD', 'BROKER_PSSWORD')
        )
        self.ha_mqtt.output_callback = self.handle_mqtt_output_command
        if not self.ha_mqtt.connect():
            exit(1)

        # Initialize managers
        try:
            self.phidgets = PhidgetsManager(
                channel_attached_external_handler=self.handle_channel_attached,
                channel_detached_external_handler=None, #self.handle_channel_detached,
                input_changed_external_handler=self.handle_input_change,
                output_changed_external_handler=self.handle_output_change
            )
            # Publish device configs for each Phidget
            #for sn in self.phidgets.get_device_serials():
            #    self.ha_mqtt.publish_device_config(sn)
        except Exception as ex:
            self.logger.exception("PhidgetsManager Failed")

            # Only try alternatives if PhidgetsManager failed
            try:
                self.gpios = GpiosManager(
                    channel_attached_external_handler=self.handle_channel_attached,
                    input_changed_external_handler=self.handle_input_change,
                    output_changed_external_handler=self.handle_output_change
                )
            except Exception as ex:
                self.logger.exception("GPIO Failed")

            try:
                self.relay = SainSmartHid(
                    channel_attached_external_handler=self.handle_channel_attached,
                    output_changed_external_handler=self.handle_output_change
                )
            except NotImplementedError:
                self.logger.warning("SainSmartHid not found")
            except RuntimeError:
                self.logger.warning("SainSmartHid failed to initialize")
                #exit(91)
            except Exception as ex:
                self.logger.exception("SainSmartHid Failed")

    def handle_channel_attached(self, sn, index, channel_type):
        self.logger.debug(f"Channel attached: {sn}/{index}: {channel_type}")
        self.ha_mqtt.publish_channel_attached(sn, index, channel_type)

    def handle_channel_detached(self, sn, index, channel_type):
        self.logger.debug(f"Channel attached: {sn}/{index}: {channel_type}")
        self.ha_mqtt.publish_channel_detached(sn, index, channel_type)

    def handle_input_change(self, sn, index, state):
        self.logger.debug(f"Input changed: {sn}/{index}: {state}")
        self.ha_mqtt.publish_input_state(sn, index, state)

    def handle_output_change(self, sn, index, state):
        self.logger.debug(f"Output changed {sn}/{index}: {state}")
        self.ha_mqtt.publish_output_state(sn, index, state)

    def handle_mqtt_output_command(self, sn, index, state):
        self.logger.debug(f"MQTT command received: for {sn}/{index}: {state}")
        # if 'sainsmart' in sn and self.relay:
        #     self.relay.set_output_state(index, state, "mqtt")
        #     #self.output_changed(sn, index, state, "mqtt")  # for now, blindly notify that output was changed
        # elif 'gpio' in sn and self.gpios:
        #     self.gpios.set_output_state(index, state, "mqtt")
        #     #self.output_changed(sn, index, state, "mqtt")  # for now, blindly notify that output was changed
        # elif self.phidgets:
        if self.phidgets:
            self.phidgets.set_output_state_from_sn_index(sn, index, state)
        if self.relay:
            self.relay.set_output_state(sn, index, state)
        #if self.gpios:
        #    self.gpios.set_output_state(sn, index, state)

    def close(self):
        if self.phidgets:
            self.phidgets.close()
        if hasattr(self, 'ha_mqtt'):
            self.ha_mqtt.client.loop_stop()
            self.ha_mqtt.client.disconnect()
