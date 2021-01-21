import socket
import pickle
import struct
import logging

from json import dumps as json_dumps

from requests import post
from requests.exceptions import RequestException


"""
For export data should look like:

For plain:
[(path, (timestamp, value)), ...]

For events:
{
    "what": "Event - deploy",
    "tags": ["deploy"],
    "when": 1467844481,
    "data": "deploy of master branch happened at Wed Jul 6 22:34:41 UTC 2016"
}
"""


logger = logging.getLogger('GraphitePusher')


class GraphitePusher:
    def __init__(self, host, port, http_url=None, tag=None, prefix=None, retention=100):
        self._host = host
        self._port = port
        self._events_url = '/'.join([http_url.rstrip('/'), 'events']) if http_url else None
        self._tag = tag
        self._prefix = prefix
        self._retention = retention
        self._batch = []

    @staticmethod
    def _add_header(message):
        header = struct.pack('!L', len(message))
        packet = header + message
        return packet

    def _get_path(self, paths):
        path = '.'.join(paths)
        if self._prefix:
            path = '.'.join([self._prefix, path])
        return path

    def add(self, timestamp, value, paths):
        path = self._get_path(paths)
        self._batch.append((path, (timestamp, value)))
        logger.debug('Adding metrics to {}, {}.'.format(path, value))
        logger.debug('Batch size {}/{}.'.format(len(self._batch), self._retention))
        if len(self._batch) < self._retention:
            return
        logger.info('Reached retention limit, pushing.')
        self.push()

    def push(self):
        try:
            batch = tuple(self._batch)
            del self._batch[:]
            batch = pickle.dumps(batch)
            batch = self._add_header(batch)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self._host, self._port))
            sock.sendall(batch)
            sock.close()
            logger.info('Successfully pushed {} bytes to {}:{}.'.format(len(batch), self._host, self._port))
        except Exception:
            logger.exception("failed to push")

    def add_event(self, what, tags, when, data):
        if not self._events_url:
            logger.warning('No http_url provided so not pushing event.')
            return

        if self._tag:
            tags.append(self._tag)

        post_data = {
            'what': what,
            'tags': tags,
            'when': when,
            'data': data
        }

        logger.info('Pushing event {}'.format(post_data))

        try:
            post(self._events_url, data=json_dumps(post_data))
        except RequestException as exc:
            logging.getLogger('GraphitePusher').exception(exc, exc_info=False)
