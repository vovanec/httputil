"""Example application.
"""

__author__ = 'vovanec@gmail.com'

import json
import logging

from pprint import pprint
from tornado import gen
from tornado import ioloop

from httputil.request_engines import async
from httputil.request_engines import sync
from httputil.request_engines import errors


DEF_REQUEST_TIMEOUT = 10
DEF_CONNECT_TIMEOUT = 3
DEF_NUM_RETRIES = 3


log = logging.getLogger('http_client')

API_BASE_URL = 'http://echo.jsontest.com'
ECHO_URL = '/key/value/one/two'
HEADERS = {'Content-Type': 'application/json'}


class SyncAPIClient(object):

    def __init__(self, connect_timeout=DEF_CONNECT_TIMEOUT,
                 request_timeout=DEF_REQUEST_TIMEOUT,
                 connection_retries=DEF_NUM_RETRIES):
        """Constructor.
        """

        self._engine = sync.SyncRequestEngine(
            API_BASE_URL, connect_timeout, request_timeout, connection_retries)

    def echo(self):

        return self._engine.request(ECHO_URL, headers=HEADERS,
                                    result_callback=lambda res: json.loads(res))


class AsyncAPIClient(object):

    def __init__(self, connect_timeout=DEF_CONNECT_TIMEOUT,
                 request_timeout=DEF_REQUEST_TIMEOUT,
                 connection_retries=DEF_NUM_RETRIES):
        """Constructor.
        """

        self._engine = async.AsyncRequestEngine(
            API_BASE_URL, connect_timeout, request_timeout, connection_retries)

    def echo(self):

        return self._engine.request(ECHO_URL, headers=HEADERS,
                                    result_callback=lambda res: json.loads(res))


@gen.coroutine
def example_async_client(api_client):
    """Example async client.
    """

    try:
        pprint((yield from api_client.echo()))
    except errors.RequestError as exc:
        log.exception('Exception occurred: %s', exc)

    yield gen.Task(lambda *args, **kwargs: ioloop.IOLoop.current().stop())


def example_sync_client(api_client):
    """Example sync client use with.
    """

    try:
        pprint(api_client.echo())
    except errors.RequestError as exc:
        log.exception('Exception occurred: %s', exc)


def main():
    """Run the examples.
    """

    logging.basicConfig(level=logging.INFO)

    example_sync_client(SyncAPIClient())
    example_async_client(AsyncAPIClient())

    io_loop = ioloop.IOLoop.current()
    io_loop.start()


if __name__ == '__main__':
    main()
