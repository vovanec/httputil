"""Request engine unit tests.

These tests require VMock library to be installed.
"""

__author__ = 'vovanec@gmail.com'

import json
import http.client
import unittest
import vmock
import vmock.matchers
from urllib.parse import urljoin

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
CONNECT_TIMEOUT = 3
REQUEST_TIMEOUT = 3


class FakeResponse(object):

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
            requests.Session, 'request')
        self.request_kwargs = {
            'verify': True, 'auth': None, 'cert': None, 'data': None,
            'timeout': REQUEST_TIMEOUT, 'headers': None}
        self._engine = sync.SyncRequestEngine(BASE_URL, CONNECT_TIMEOUT,
                                              REQUEST_TIMEOUT, None)

    def test_ok(self):

        expected = {'status': 'ok'}
        response = FakeResponse(http.client.OK, json.dumps(expected))

        self.mock_request('GET', urljoin(BASE_URL, '/blah'),
                          **self.request_kwargs).returns(response)

        self.assertDictEqual(
            self._engine.request('/blah', result_callback=json.loads), expected)

    def test_with_headers(self):

        expected = {'status': 'ok'}
        response = FakeResponse(http.client.OK, json.dumps(expected))

        headers = {'Content-Type': 'application/json'}
        self.request_kwargs['headers'] = headers
        self.mock_request('GET', urljoin(BASE_URL, '/blah'),
                          **self.request_kwargs).returns(response)

        self.assertDictEqual(
            self._engine.request('/blah', result_callback=json.loads,
                                 headers=headers), expected)

    def test_malformed_response(self):

        response = FakeResponse(http.client.OK, '--Not JSON--')
        self.mock_request('GET', urljoin(BASE_URL, '/blah'),
                          **self.request_kwargs).returns(response)
        with self.assertRaises(errors.MalformedResponse):
            self._engine.request('/blah', result_callback=json.loads)

    def test_http_client_error(self):

        response = FakeResponse(
            http.client.BAD_REQUEST,
            json.dumps({'message': 'Data not found'}))
        self.mock_request('GET', urljoin(BASE_URL, '/blah'),
                          **self.request_kwargs).returns(response)

        with self.assertRaises(errors.ClientError):
            self._engine.request('/blah', result_callback=json.loads)

    def test_http_server_error(self):

        response = FakeResponse(http.client.SERVICE_UNAVAILABLE)
        self.mock_request('GET', urljoin(BASE_URL, '/blah'),
                          **self.request_kwargs).returns(response)

        with self.assertRaises(errors.ServerError):
            self._engine.request('/blah', result_callback=json.loads)

    def test_communication_error(self):

        self.mock_request = self.mock_request(vmock.matchers.any_args())
        self.mock_request.raises(
            requests.exceptions.RequestException('No route to host'))

        with self.assertRaises(errors.CommunicationError):
            self._engine.request('/blah', result_callback=json.loads)


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
            make_fetch_impl(http.client.OK, json.dumps(expected)))

        response = yield from self._engine.request(
            '/blah', result_callback=json.loads)
        self.assertDictEqual(response, expected)

    @tornado.testing.gen_test
    def test_malformed_response(self):

        self.mock_fetch_impl(
            vmock.matchers.any_args()).does(
            make_fetch_impl(http.client.OK, '--asdasd---'))

        with self.assertRaises(errors.MalformedResponse):
            yield from self._engine.request('/blah', result_callback=json.loads)

    @tornado.testing.gen_test
    def test_client_error(self):

        error_body = json.dumps({'message': 'Method not found'})

        self.mock_fetch_impl(
            vmock.matchers.any_args()).does(
            make_fetch_impl(http.client.NOT_FOUND, error_body))

        with self.assertRaises(errors.ClientError):
            yield from self._engine.request(
                '/blah', result_callback=json.loads)

    @tornado.testing.gen_test
    def test_server_error(self):

        self.mock_fetch_impl(
            vmock.matchers.any_args()).does(
            make_fetch_impl(http.client.SERVICE_UNAVAILABLE))

        with self.assertRaises(errors.ServerError):
            yield from self._engine.request('/blah', result_callback=json.loads)

    @tornado.testing.gen_test
    def test_communication_error(self):

        self.mock_fetch_impl(
            vmock.matchers.any_args()).does(
            make_fetch_impl(CURL_ERROR, 'No route to host'))

        with self.assertRaises(errors.CommunicationError):
            yield from self._engine.request('/blah', result_callback=json.loads)


if __name__ == '__main__':

    unittest.main()
