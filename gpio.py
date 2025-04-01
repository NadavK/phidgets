from signal import pause
from gpiozero import Button, LED
import traceback
import logging

from utils import get_device_id

# RPi B (26 pins)
BCM_INPUT_IDS = [2, 3, 4, 14, 15, 17, 18, 27, 22, 23, 24, 10, 9, 25, 11, 8, 7]  # total 17
BCM_OUTPUT_IDS = []  # total 0


# Manages all GPIOs
class GpiosManager:
    manager22 = None
    buttons = []    # Inputs
    leds = []       # Outputs
    sn = ""

    # Initialization
    def __init__(self,
                 channel_attached_external_handler=None,
                 input_changed_external_handler=None,
                 output_changed_external_handler=None):
        try:
            self.logger = logging.getLogger(self.__class__.__name__)
            self.logger.info('Starting')
            self.channel_attached_external_handler = channel_attached_external_handler
            self.input_changed_external_handler = input_changed_external_handler
            self.output_changed_external_handler = output_changed_external_handler
            self.sn = get_device_id()
            # Initialize and publish inputs
            for id in BCM_INPUT_IDS:
                button = Button("BCM" + str(id))
                button.when_pressed = self.button_state_changed
                button.when_released = self.button_state_changed
                self.buttons.append(button)
                if self.channel_attached_external_handler:
                    self.channel_attached_external_handler(self.sn, id, 'Input')
            # Initialize and publish outputs
            for id in BCM_OUTPUT_IDS:
                led = LED("BCM" + str(id))
                self.leds.append(led)
                if self.channel_attached_external_handler:
                    self.channel_attached_external_handler(self.sn, id, 'Output')
        except Exception as e:
            traceback.print_tb(e.__traceback__)
            self.logger.exception('init')
            raise e

    def button_state_changed(self, button):
        pin = button.pin.number
        state = button.is_active
        print(pin, state, button)

        self.logger.info("Notifying GPIO %s/%i state changed to: %r" % (self.sn, pin, state))
        if self.input_changed_external_handler:
            self.input_changed_external_handler(self.sn, pin, state)

    def get_states(self):
        for button in self.buttons:
            self.button_state_changed(button)
        for led in self.leds:
            self.led_state_changed(led)

    def set_output_state(self, index, state, force_notify=False):
        for led in self.leds:
            if str(led.pin.number) == str(index):
                if state:
                    led.on()
                else:
                    led.off()
                return

        self.logger.exception('Failed finding output index {}]'.format(index))

    def led_state_changed(self, led):
        pin = led.pin.number
        state = led.is_lit
        print(pin, state, led)

        self.logger.info("Notifying GPIO %s/%i state changed to: %r" % (self.sn, pin, state))
        if self.output_changed_external_handler:
            self.output_changed_external_handler(self.sn, pin, state)


def main():
    gpios = GpiosManager(None, None)
    import time

    while True:
        gpios.set_output_state(1, 1, False)
        print('ready')
        time.sleep(1)
        gpios.set_output_state(1, 0, False)
        print('ready')
        time.sleep(1)
    pause()


if __name__ == "__main__":
    main()
