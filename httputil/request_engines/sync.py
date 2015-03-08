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


SUPPORTED_PROTOCOLS = {'http'}


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
            s = requests.Session()
            try:
                for protocol in SUPPORTED_PROTOCOLS:
                    s.mount('%s://' % (protocol,),
                            requests.adapters.HTTPAdapter(max_retries=False))

                response = s.request(method, url, data=data,
                                     timeout=self._connect_timeout)
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
