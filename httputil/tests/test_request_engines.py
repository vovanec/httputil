"""Request engine unit tests.

These tests require VMock library to be installed.
"""

__author__ = 'vovanec@gmail.com'

import ujson
import http.client
import unittest
import vmock
import vmock.matchers

import requests.exceptions
import requests.models
import requests.sessions
import tornado.testing
import tornado.httpclient
import tornado.curl_httpclient

from httputil.request_engines import async
from httputil.request_engines import errors
from httputil.request_engines import sync


CURL_ERROR = 599
BASE_URL = 'http://api.com'


class FakeReposne(object):

    """Fake requests.Response."""

    def __init__(self, status_code, content=None):

        self.status_code = status_code
        self.content = content


class TestSyncClient(unittest.TestCase):

    """Test synchronous client."""

    def setUp(self):

        self.mock = vmock.VMock()
        self.addCleanup(self.mock.tear_down)
        self.mock_request = self.mock.stub_method(
            requests.Session, 'request')(vmock.matchers.any_args())
        self._engine = sync.SyncRequestEngine(BASE_URL, 3, 3, None)

    def test_ok(self):

        expected = {'status': 'ok'}
        response = FakeReposne(http.client.OK, ujson.dumps(expected))

        self.mock_request.returns(response)
        self.assertDictEqual(self._engine.request('/blah'), expected)

    def test_malformed_response(self):

        response = FakeReposne(http.client.OK, '--Not JSON--')
        self.mock_request.returns(response)

        with self.assertRaises(errors.MalformedResponse):
            self._engine.request('/blah')

    def test_http_client_error(self):

        response = FakeReposne(
            http.client.BAD_REQUEST,
            ujson.dumps({'message': 'Data not found'}))
        self.mock_request.returns(response)

        with self.assertRaises(errors.ClientError):
            self._engine.request('/blah')

    def test_http_server_error(self):

        response = FakeReposne(http.client.SERVICE_UNAVAILABLE)
        self.mock_request.returns(response)

        with self.assertRaises(errors.ServerError):
            self._engine.request('/blah')

    def test_communication_error(self):

        self.mock_request.raises(
            requests.exceptions.RequestException('No route to host'))

        with self.assertRaises(errors.CommunicationError):
            self._engine.request('/blah')


class FakeHTTPResponse(object):

    """Fake tornado.httpclient.HTTPResponse."""

    def __init__(self, code, body=None, error=None):

        self.code = code
        self.body = body
        self.error = error


def make_fetch_impl(code, body=None):
    """Create fetch_impl() substitution for tornado.httpclient.

    :param int code: HTTP code.
    :param str body: response body.
    """

    error = None
    response = FakeHTTPResponse(code, body, error)

    if code >= 400:
        error = tornado.httpclient.HTTPError(code, body)
        response.error = error
        error.response = response

    def fetch_impl(_, callback):
        callback(FakeHTTPResponse(code, body, error))

    return fetch_impl


class TestAsyncClient(tornado.testing.AsyncTestCase):

    """Test asynchronous client(coroutine style)."""

    def setUp(self):

        super().setUp()

        self.mock = vmock.VMock()
        self.addCleanup(self.mock.tear_down)

        self.mock_fetch_impl = self.mock.stub_method(
            tornado.curl_httpclient.CurlAsyncHTTPClient, 'fetch_impl')

        self._engine = async.AsyncRequestEngine(BASE_URL, 3, 3, None)

    @tornado.testing.gen_test
    def test_ok(self):

        expected = {'status': 'ok'}
        self.mock_fetch_impl(
            vmock.matchers.any_args()).does(
            make_fetch_impl(http.client.OK, ujson.dumps(expected)))

        response = yield from self._engine.request('/blah')
        self.assertDictEqual(response, expected)

    @tornado.testing.gen_test
    def test_malformed_response(self):

        self.mock_fetch_impl(
            vmock.matchers.any_args()).does(
            make_fetch_impl(http.client.OK, '--asdasd---'))

        with self.assertRaises(errors.MalformedResponse):
            yield from self._engine.request('/blah')

    @tornado.testing.gen_test
    def test_client_error(self):

        error_body = ujson.dumps({'message': 'Method not found'})

        self.mock_fetch_impl(
            vmock.matchers.any_args()).does(
            make_fetch_impl(http.client.NOT_FOUND, error_body))

        with self.assertRaises(errors.ClientError):
            yield from self._engine.request('/blah')

    @tornado.testing.gen_test
    def test_server_error(self):

        self.mock_fetch_impl(
            vmock.matchers.any_args()).does(
            make_fetch_impl(http.client.SERVICE_UNAVAILABLE))

        with self.assertRaises(errors.ServerError):
            yield from self._engine.request('/blah')

    @tornado.testing.gen_test
    def test_communication_error(self):

        self.mock_fetch_impl(
            vmock.matchers.any_args()).does(
            make_fetch_impl(CURL_ERROR, 'No route to host'))

        with self.assertRaises(errors.CommunicationError):
            yield from self._engine.request('/blah')


class TestAsyncClientWithCallback(tornado.testing.AsyncTestCase):

    """Test asynchronous client(callback style)."""

    def setUp(self):

        super().setUp()

        self.mock = vmock.VMock()
        self.addCleanup(self.mock.tear_down)

        self.mock_fetch_impl = self.mock.stub_method(
            tornado.curl_httpclient.CurlAsyncHTTPClient, 'fetch_impl')

        self._engine = async.AsyncRequestEngine(BASE_URL, 3, 3, None)

    def test_ok(self):

        expected = {'status': 'ok'}
        self.mock_fetch_impl(
            vmock.matchers.any_args()).does(
            make_fetch_impl(http.client.OK, ujson.dumps(expected)))

        def cb(response):
            self.assertDictEqual(response, expected)
            self.stop()

        self._engine.request('/blah', callback=cb)
        self.wait()

    def test_malformed_response(self):

        self.mock_fetch_impl(
            vmock.matchers.any_args()).does(
            make_fetch_impl(http.client.OK, '--asdasd---'))

        def cb(response):
            self.assertIsInstance(response, errors.MalformedResponse)
            self.stop()

        self._engine.request('/blah', callback=cb)
        self.wait()

    def test_client_error(self):

        error_body = ujson.dumps({'message': 'Method not found'})

        self.mock_fetch_impl(
            vmock.matchers.any_args()).does(
            make_fetch_impl(http.client.NOT_FOUND, error_body))

        def cb(response):
            self.assertIsInstance(response, errors.ClientError)
            self.stop()

        self._engine.request('/blah', callback=cb)
        self.wait()

    def test_server_error(self):

        self.mock_fetch_impl(
            vmock.matchers.any_args()).does(
            make_fetch_impl(http.client.SERVICE_UNAVAILABLE))

        def cb(response):
            self.assertIsInstance(response, errors.ServerError)
            self.stop()

        self._engine.request('/blah', callback=cb)
        self.wait()

    def test_communication_error(self):

        self.mock_fetch_impl(
            vmock.matchers.any_args()).does(
            make_fetch_impl(CURL_ERROR, 'No route to host'))

        def cb(response):
            self.assertIsInstance(response, errors.CommunicationError)
            self.stop()

        self._engine.request('/blah', callback=cb)
        self.wait()


if __name__ == '__main__':

    unittest.main()
