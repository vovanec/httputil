"""Asynchronous request engine."""

__author__ = 'vovanec@gmail.com'

import ujson

from tornado import curl_httpclient
from tornado import gen
from tornado import httpclient

from .base_engine import BaseRequestEngine
from .errors import ClientError
from .errors import CommunicationError
from .errors import MalformedResponse
from .errors import ServerError


# Configure async engine to use CURL client whenever possible.
httpclient.AsyncHTTPClient.configure(curl_httpclient.CurlAsyncHTTPClient)


class AsyncRequestEngine(BaseRequestEngine):

    """Asynchronous request engine.

    Uses Tornado asynchronous client to make HTTP requests.

    """

    def __init__(self, api_base_url, connect_timeout, request_timeout,
                 conn_retries):
        """Constructor.

        :param str api_base_url: API base URL.
        :param int connect_timeout: connection timeout.
        :param int request_timeout: request timeout.
        :param int|None conn_retries: The number of retries on connection
               error. If None - no retries.
        """

        super().__init__(
            api_base_url, connect_timeout, request_timeout, conn_retries)

        self._client = httpclient.AsyncHTTPClient()

    def _request(self, url, *, method='GET', data=None, callback=None):
        """Perform asynchronous request.

        :param str url: request URL.
        :param str method: request method.
        :param object data: JSON-encodable object.
        :param object -> None callback: finish callback

        :rtype: dict
        :raise: APIError

        """

        request = self._prepare_request(url, method, data)
        if callback is not None:
            return self._request_with_callback(request, callback)

        return self._request_with_coroutine(request)

    def _request_with_callback(self, request, callback):
        """Asynchronous request with callback.

        :param httpclient.HTTPRequest request: HTTP request
        :param object -> None callback: finish callback

        :raise: APIError

        """

        if self._conn_retries is not None:
            self._log.debug('Error retries don\'t are not yet supported '
                            'with callback interface.')

        def handle_response(resp):

            if isinstance(resp.error, httpclient.HTTPError):
                resp_body = resp.body if resp is not None else None
                if resp.error.code == 599:
                    callback(CommunicationError(resp.error))
                elif 400 <= resp.error.code < 500:
                    callback(ClientError(resp.code, resp_body))
                else:
                    callback(ServerError(resp.code, resp_body))
            else:
                try:
                    result = ujson.loads(resp.body)
                except (ValueError, TypeError) as err:
                    self._log.warning('Could not decode JSON body: %s', err)
                    result = MalformedResponse(err)

                callback(result)

        self._client.fetch(request, callback=handle_response)

    def _request_with_coroutine(self, request):
        """Asynchronous request using coroutine.

        :param httpclient.HTTPRequest request: HTTP request

        :rtype: dict
        :raise: APIError

        """

        retries_left = self._conn_retries

        while True:
            try:
                response = yield self._client.fetch(request)
                try:
                    return ujson.loads(response.body)
                except (ValueError, TypeError) as err:
                    raise MalformedResponse(err) from None
            except httpclient.HTTPError as err:
                resp_body = err.response.body \
                    if err.response is not None else None
                if err.code == 599:
                    if self._conn_retries is None or retries_left <= 0:
                        raise CommunicationError(err) from None
                    else:
                        retries_left -= 1
                        retry_in = (self._conn_retries - retries_left) * 2
                        self._log.warning('Server communication error: %s. '
                                          'Retrying in %s seconds.', err,
                                          retry_in)
                        yield gen.sleep(retry_in)
                        continue
                elif 400 <= err.code < 500:
                    raise ClientError(err.code, resp_body) from None

                raise ServerError(err.code, resp_body) from None

    def _prepare_request(self, url, method, data):
        """Prepare HTTP request.

        :param str url: request URL.
        :param str method: request method.
        :param object data: JSON-encodable object.

        :rtype: httpclient.HTTPRequest

        """

        headers = {'Content-Type': 'application/json'}
        request = httpclient.HTTPRequest(
            url=url, method=method, headers=headers, body=data,
            connect_timeout=self._connect_timeout,
            request_timeout=self._request_timeout)

        return request
