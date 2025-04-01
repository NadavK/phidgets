# main.py
import atexit
import logging
import logging.config
import settings
from app import PhidgetApp
import time


class Main:
    def __init__(self):
        self.app = None
        atexit.register(self.exit_handler)

    def start(self):
        logging.config.dictConfig(settings.LOGGING)
        logger = logging.getLogger(__name__)
        logger.info('=================== PhidgetS v0.9 starting ===================')

        self.app = PhidgetApp()

        # Keep the program running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

    def exit_handler(self):
        logger = logging.getLogger(__name__)
        logger.info('=================== PhidgetS Exiting ===================')
        if self.app:
            self.app.close()


if __name__ == "__main__":
    Main().start()