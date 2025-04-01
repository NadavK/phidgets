# ha_mqtt.py
import paho.mqtt.client as mqtt
import logging
import json


class HAMQTTClient:
    def __init__(self, broker_host, broker_port=1883, username=None, password=None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.client = mqtt.Client()
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.username = username
        self.password = password
        self.output_callback = None
        self.attached_channels = {}  # Track attached channels per device

    def connect(self):
        self.logger.info(f"Connecting to MQTT broker {self.broker_host}:{self.broker_port} using {self.username}")

        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        # Set username and password if provided
        if self.username and self.password:
            self.client.username_pw_set(self.username, self.password)
        try:
            self.client.connect(self.broker_host, int(self.broker_port), 60)
            self.client.loop_start()
            return True
        except Exception as e:
            self.logger.fatal(f"Error connecting to MQTT broker {self.broker_host}:{self.broker_port} {e}", exc_info=True)
            return False

    def on_connect(self, client, userdata, flags, rc):
        self.logger.info(f"Connected to MQTT broker with result code {rc}")
        # Subscribe to all output command topics
        self.client.subscribe("phidget/+/output/+/command")

    def on_message(self, client, userdata, msg):
        try:
            if msg.topic.startswith("phidget/") and "/output/" in msg.topic:
                parts = msg.topic.split("/")
                if len(parts) == 5 and parts[4] == "command":
                    sn = parts[1]
                    index = int(parts[3])
                    state = msg.payload.decode() == "ON"
                    if self.output_callback:
                        self.output_callback(sn, index, state)
        except Exception as e:
            self.logger.error(f"Error processing MQTT message: {e}")

    def publish_channel_attached(self, sn, index, channel_type):
        """Publish channel attached status and config"""
        # Track attached channel
        if sn not in self.attached_channels:
            self.attached_channels[sn] = set()
        self.attached_channels[sn].add(index)

        # Publish status with channel type in topic
        channel_type = channel_type.lower()
        topic = f"phidget/{sn}/{channel_type}/{index}/status"
        payload = json.dumps({
            "state": "attached",
            "device_id": sn,
            "channel": index,
            "type": channel_type,
        })
        self.client.publish(topic, payload, retain=True)

        # Publish config
        self.publish_channel_config(sn, index, channel_type)

    def publish_channel_detached(self, sn, index, channel_type):
        """Publish channel detached status"""
        # Remove from tracked channels
        if sn in self.attached_channels:
            self.attached_channels[sn].discard(index)
            if not self.attached_channels[sn]:
                del self.attached_channels[sn]

        channel_type = channel_type.lower()
        topic = f"phidget/{sn}/{channel_type}/{index}/status"
        payload = json.dumps({
            "state": "detached",
            "device_id": sn,
            "channel": index,
            "type": channel_type
        })
        self.client.publish(topic, payload, retain=True)

    def publish_channel_config(self, sn, index, channel_type):
        """Publish Home Assistant MQTT discovery config for a single channel"""
        base_topic = f"homeassistant"
        device = {
            "identifiers": [f"phidget_{sn}"],
            "name": f"Phidget {sn}",
            "model": "Phidget Interface Kit",
            "manufacturer": "Phidgets"
        }

        channel_type = channel_type.lower()
        if channel_type == 'input':
            # Input binary sensor config
            config = {
                "name": f"Phidget {sn} {channel_type} {index}",
                "unique_id": f"phidget_{sn}_{channel_type}_{index}",
                "state_topic": f"phidget/{sn}/{channel_type}/{index}/state",
                "value_template": "{{value_json.state}}",
                #"device_class": "binary_sensor",
                "payload_on": "ON",
                "payload_off": "OFF",
                "device": device
            }
            config_topic = f"{base_topic}/binary_sensor/phidget_{sn}_{channel_type}_{index}/config"
        else:
            # Output switch config
            config = {
                "name": f"Phidget {sn} {channel_type} {index}",
                "unique_id": f"phidget_{sn}_{channel_type}_{index}",
                "command_topic": f"phidget/{sn}/{channel_type}/{index}/command",
                "state_topic": f"phidget/{sn}/{channel_type}/{index}/state",
                "value_template": "{{value_json.state}}",
                "state_class": "measurement",  # Changed from device_class
                #"device_class": "switch",
                "payload_on": "ON",
                "payload_off": "OFF",
                "device": device
            }
            config_topic = f"{base_topic}/switch/phidget_{sn}_{channel_type}_{index}/config"

        self.client.publish(config_topic, json.dumps(config), retain=True)

    def publish_input_state(self, sn, index, state):
        """Publish input state change"""
        print(f'Publish input state change: {sn}/{index} --> {state}')
        topic = f"phidget/{sn}/input/{index}/state"
        payload = json.dumps({
            "state": "ON" if state else "OFF",
            "device_id": sn,
            "channel": index
        })
        self.client.publish(topic, payload, retain=True)

    def publish_output_state(self, sn, index, state):
        """Publish output state change"""
        topic = f"phidget/{sn}/output/{index}/state"
        payload = json.dumps({
            "state": "ON" if state else "OFF",
            "device_id": sn,
            "channel": index,
        })
        print(f'Publish output state change: {topic} --> {payload}')
        self.logger.info(f'Publishing to {topic}: {payload}')
        self.client.publish(topic, payload, retain=True)
