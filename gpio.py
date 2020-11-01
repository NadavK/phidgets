from signal import pause
from gpiozero import Button, LED
import traceback
import logging

# RPi B (26 pins)
from utils import get_sn, generate_request_id

BCM_INPUT_IDS = [2, 3, 4, 14, 15, 17, 18, 27, 22, 23, 24, 10, 9, 25, 11, 8, 7]  # total 17
BCM_OUTPUT_IDS = []  # total 0


# Manages all GPIOs
class GpiosManager:
    manager22 = None
    buttons = []    # Inputs
    leds = []       # Outputs
    input_changed_external_handler = None
    sn = ""

    # Initialization
    def __init__(self, input_changed_external_handler, output_changed_external_handler):
        try:
            self.logger = logging.getLogger(self.__class__.__name__)
            self.logger.info('Starting')
            self.input_changed_external_handler = input_changed_external_handler
            self.output_changed_external_handler = output_changed_external_handler
            self.sn = get_sn()
            for id in BCM_INPUT_IDS:
                button = Button("BCM" + str(id))
                button.when_pressed = self.button_state_changed
                button.when_released = self.button_state_changed
                self.buttons.append(button)
            for id in BCM_OUTPUT_IDS:
                led = LED("BCM" + str(id))
                self.leds.append(led)

        except Exception as e:
            traceback.print_tb(e.__traceback__)
            self.logger.exception('init')

    def button_state_changed(self, button, request_id=None):
        if not request_id:
            request_id = generate_request_id() + '_state_change'

        pin = button.pin.number
        state = button.is_active
        print(pin, state, button)

        self.logger.info("Notifying GPIO %s/%i state changed to: %r [%s]" % (self.sn, pin, state, request_id))
        if self.input_changed_external_handler:
            self.input_changed_external_handler(self.sn, pin, state, request_id)

    def get_states(self, request_id):
        for button in self.buttons:
            self.button_state_changed(button, request_id)
        for led in self.leds:
            self.led_state_changed(led, request_id)

    def set_output_state(self, index, state, request_id, force_notify=False):
        for led in self.leds:
            if str(led.pin.number) == str(index):
                if state:
                    led.on()
                else:
                    led.off()
                return

        self.logger.exception('Failed finding output index {} [{}]'.format(index, request_id))

    def led_state_changed(self, led, request_id=None):
        if not request_id:
            request_id = generate_request_id() + '_state_change'

        pin = led.pin.number
        state = led.is_lit
        print(pin, state, led)

        self.logger.info("Notifying GPIO %s/%i state changed to: %r [%s]" % (self.sn, pin, state, request_id))
        if self.output_changed_external_handler:
            self.output_changed_external_handler(self.sn, pin, state, request_id)


def main():
    gpois = GpiosManager(None)
    print('ready')
    pause()


if __name__ == "__main__":
    main()
