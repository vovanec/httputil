"""Synchronous request engine."""

__author__ = 'vovanec@gmail.com'


import requests.adapters
import requests.exceptions
import requests.models
import time
import ujson

from .base import BaseRequestEngine
from .errors import ClientError
from .errors import CommunicationError
from .errors import MalformedResponse
from .errors import ServerError


class SyncRequestEngine(BaseRequestEngine):

    """Synchronous request engine.

    Uses requests module to make HTTP requests.

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

    def _request(self, url, *, method='GET', data=None, **kwargs):
        """Perform synchronous request.

        :param str url: request URL.
        :param str method: request method.
        :param object data: JSON-encodable object.
        :param object -> None callback: finish callback

        :rtype: dict
        :raise: APIError

        """

        retries_left = self._conn_retries

        while True:
            s = self._make_session()
            try:
                cert = None
                if self._client_cert and self._client_key:
                    cert = (self._client_cert, self._client_key)
                elif self._client_cert:
                    cert = self._client_cert

                verify = self._ca_certs
                if self._ca_certs is not None:
                    verify = self._verify_cert

                auth = None
                if self._username and self._password:
                    auth = (self._username, self._password)

                response = s.request(method, url, data=data,
                                     timeout=self._connect_timeout,
                                     cert=cert,
                                     verify=verify,
                                     auth=auth)
                """:type: requests.models.Response
                """
                if 400 <= response.status_code < 500:
                    raise ClientError(
                        response.status_code, response.content)
                elif response.status_code >= 500:
                    raise ServerError(
                        response.status_code, response.content)

                try:
                    return ujson.loads(response.content)
                except (ValueError, TypeError) as err:
                    raise MalformedResponse(err) from None

            except (requests.exceptions.RequestException,
                    requests.exceptions.BaseHTTPError) as exc:
                if self._conn_retries is None or retries_left <= 0:
                    raise CommunicationError(exc) from None
                else:
                    retries_left -= 1
                    retry_in = (self._conn_retries - retries_left) * 2
                    self._log.warning('Server communication error: %s. '
                                      'Retrying in %s seconds.', exc, retry_in)
                    time.sleep(retry_in)
                    continue
            finally:
                s.close()

    @staticmethod
    def _make_session():

        sess = requests.Session()
        sess.mount('http://', requests.adapters.HTTPAdapter(max_retries=False))
        sess.mount('https://', requests.adapters.HTTPAdapter(max_retries=False))
        return sess