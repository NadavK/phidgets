import atexit
import cherrypy
import logging
import logging.config
import sys

import settings
from app import PhidgetApp


class Main:
    server = None

    def __init__(self):
        # signal.signal(signal.SIGINT, self.handler_stop_signals)  was never called
        # signal.signal(signal.SIGTERM, self.handler_stop_signals) was never called
        atexit.register(self.exit_handler)

    def start(self):
        logging.config.dictConfig(settings.LOGGING)
        logger = logging.getLogger(__name__)

        logger.info('=================== PhidgetServer starting ===================')
        logger.info(__name__)
        logger.info(sys.argv)
        if len(sys.argv) < 2:
            logger.info('PhdigetServer expects ip:port param %s' % sys.argv)
            exit()

        if ':' in sys.argv[1]:
            host, port = sys.argv[1].split(':')
            cherrypy.config.update({'server.socket_port': int(port)})
        else:
            host = sys.argv[1]
        cherrypy.config.update({'server.socket_host': host})
        self.server = PhidgetApp()
        #for phidget in settings.PHIDGETS:
        #    server.conect(phidget, settings.CALLBACK_URL)
        cherrypy.quickstart(self.server, '/', config={
            'global': {
                'engine.autoreload.on': False
            },
            '/': {
                'tools.gzip.on': False
            }
        })

        #app.route("/connect/<sn>", method='POST')(app.connect)
        ##app.route("/get_states/<sn>")(app.get_states)
        #app.route("/set_state/<sn>/<index>/<state>", method='POST')(app.set_state)

    def exit_handler(self):
        logger = logging.getLogger(__name__)
        logger.info('=================== PhidgetServer Exiting ===================')
        if self.server:
            self.server.close()

    # was never called...
    #   def handler_stop_signals(self, signum, frame):
    #    print("Caught termination signal:)", signum, frame)


if __name__ == "__main__":
    Main().start()
