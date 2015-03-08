"""Base request engine."""

__author__ = 'vovanec@gmail.com'

import logging


class BaseRequestEngine(object):

    """Base class for HTTP request engine."""

    def __init__(self, api_base_url, connect_timeout, request_timeout,
                 conn_retries):
        """Constructor.

        :param str api_base_url: API base URL.
        :param int connect_timeout: connection timeout.
        :param int request_timeout: request timeout.
        :param int|None conn_retries: The number of retries on connection
               error. If None - no retries.
        """

        self._connect_timeout = connect_timeout
        self._request_timeout = request_timeout
        self._api_base_url = api_base_url
        self._conn_retries = conn_retries
        self._log = logging.getLogger(self.__class__.__name__)

    def request(self, url, *, method='GET', data=None, **kwargs):
        """Perform request.

        :param str url: request URL.
        :param str method: request method.
        :param object data: JSON-encodable object.

        :rtype: dict
        :raise: APIError

        """

        return self._request(self._api_base_url + url,
                             method=method, data=data, **kwargs)

    def _request(self, url, *, method='GET', data=None, **kwargs):
        """Perform request. Subclasses must implement this.

        :param str url: request URL.
        :param str method: request method.
        :param object data: JSON-encodable object.

        :rtype: dict
        :raise: APIError

        """

        raise NotImplementedError
