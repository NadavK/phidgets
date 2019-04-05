import queue
import uuid

import requests
import threading
import logging


class RequestDetails:
    REQUEST_ID_HEADER = 'X-Request-ID'

    def __init__(self, method, url, json, token, request_id=None):
        self.method = method.upper()
        self.url = url
        self.json = json
        self.token = token
        self.request_id = request_id

        if not self.request_id:
            self.request_id = uuid.uuid4().hex
        self.headers = {self.REQUEST_ID_HEADER: request_id}
        if self.token:
            self.headers['Authorization'] = 'Token ' + token

    def __str__(self):
        return '%s %s: %s [%s]' % (self.method, self.url, self.json, self.request_id)


class AsyncHttp:
    q = queue.Queue(100)
    logger = logging.getLogger(__name__)

    def __init__(self):
        worker = threading.Thread(target=self.process_request)
        worker.setDaemon(True)
        worker.start()

    # Generates an async request
    def request(self, method, url, json, token, request_id):
        try:
            details = RequestDetails(method, url, json, token, request_id)
            self.logger.debug('queuing send request: %s' % details)
            self.q.put_nowait(details)
            return True
        except queue.Full:
            self.logger.exception('Queue full')
            return False
        except Exception:
            self.logger.exception('Queue failed')
            return False

    def process_request(self):
        while True:
            try:
                details = self.q.get()
                self.logger.debug('Sending request: %s' % details)
                r = requests.request(method=details.method, url=details.url, json=details.json, headers=details.headers)
                r.raise_for_status()
                self.logger.debug('Request response code: %s <-- %s ' % (r.status_code, details))
            except requests.exceptions.RequestException as e:
                self.logger.error('notify request failed on library exception \'%s\' for %s: ' % (type(e).__name__, details))
            except Exception:
                self.logger.exception('notify request failed on exception')
            self.q.task_done()
