import cherrypy
import logging
import json
import uuid

from asynchttp import AsyncHttp
from phidget_io import PhidgetsManager
from settings import CALLBACK_URLS

HTTP_REQUEST_ID_HEADER = 'Http-X-Request-Id'


class PhidgetApp:

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.phidgets = PhidgetsManager(self.input_changed, self.output_changed)
        self.callback_urls = CALLBACK_URLS     # key=callback_url, value=token
        self.asyncHttp = AsyncHttp()

        request_id = uuid.uuid4().hex + '_PhidgetApp_init'
        for callback_url, token in self.callback_urls.items():
            url = callback_url + 'outputs/outputs/'
            self.logger.debug("Requesting default outputs, calling %s [%s]" % (url, request_id))
            self.asyncHttp.request("get", url, {}, token, request_id)

    # Was never called
    #def __del__(self):
    #    self.logger('PhidgetApp d\'tor')
    #    self.close()

    def close(self):
        self.phidgets.close()
        #self.logger('PhidgetApp close')     # caused an exception

    @cherrypy.expose
    @cherrypy.tools.allow(methods=['POST'])
    @cherrypy.tools.json_in()
    def default_outputs(self, sn):
        """
        Sets default output states
        Is used to set multiple outputs when Django/Phidget loads
        'states' - string-based bit-mask for initial output states
        """

        data = cherrypy.request.json
        states = data.get('states')
        request_id = cherrypy.request.headers.get(HTTP_REQUEST_ID_HEADER)
        self.logger.info('Received request set default states for Phidget #%s outputs: \'%s\' [%s]' % (sn, states, request_id))
        self.phidgets.set_default_output_states(sn, states, request_id=request_id)

    @cherrypy.expose
    @cherrypy.tools.allow(methods=['GET'])
    @cherrypy.tools.json_in()
    def states(self):
        """"
        Fires Notifying State Change callback url for each input and output channel
        """
        request_id = cherrypy.request.headers.get(HTTP_REQUEST_ID_HEADER)
        self.logger.info('Received get states request for all Phidgets [%s]' % request_id)
        try:
            self.phidgets.get_states(request_id)
        except Exception as ex:
            self.logger.exception("")
            raise cherrypy.HTTPError(500, ex)

    @cherrypy.expose
    @cherrypy.tools.allow(methods=['POST'])
    @cherrypy.tools.json_in()
    def output(self, sn, index, state):
        """
        Set the phidget output state
        :param sn:
        :param index:
        :param state:
        :return: None
        """
        try:
            state = json.loads(state)
            request_id = cherrypy.request.headers.get(HTTP_REQUEST_ID_HEADER)
            self.logger.info('Received set output state #%s/%s: %r [%s]' % (sn, index, state, request_id))
            self.phidgets.set_output_state_from_sn_index(sn, index, state, request_id)
            return "OK"
        except Exception as ex:
            self.logger.exception("")
            raise cherrypy.HTTPError(500, ex)

    def input_changed(self, sn, index, state, request_id=None):
        self._changed('Input', 'inputs/input/', sn, index, state, request_id)

    def output_changed(self, sn, index, state, request_id=None):
        self._changed('Output', 'outputs/output_changed/', sn, index, state, request_id)

    def _changed(self, type, url_path, sn, index, state, request_id=None):
        #self.logger.debug("Received changed event: %s %s/%s: %s [%s]" % (type, sn, index, state, request_id))
        if request_id is None:
            request_id = uuid.uuid4().hex
        #self.logger.debug("IOChanged %s %i/%i: %s [%s]" % (type, sn, index, state, request_id))
        for callback_url, token in self.callback_urls.items():
            url = callback_url + url_path
            self.logger.debug("%s changed %s/%s: %s, calling %s [%s]" % (type, sn, index, state, url, request_id))
            self.asyncHttp.request("post", url, {'sn': sn, 'index': index, 'state': state}, token, request_id)
