"""Request engine errors."""

__author__ = 'vovanec@gmail.com'

import logging
import ujson
import http.client


class APIError(Exception):

    """Base Entitlement API error."""


class CommunicationError(APIError):

    """Communication problem with Entitlement API server."""


class MalformedResponse(APIError):

    """Server responded with data which client could not understand."""


class HTTPError(APIError):

    """Entitlement API server returned HTTP error."""

    def __init__(self, code, response_body=None):
        """Constructor.

        :param int code: HTTP code.
        :param str response_body: HTTP response body.

        """

        self.code = code
        message = http.client.responses.get(code, 'Unknown')
        if response_body:
            try:
                message = ujson.loads(response_body)['message']
            except (ValueError, TypeError, KeyError) as err:
                logging.getLogger(
                    self.__class__.__name__).error(
                    'Could not decode error JSON body: %s', err)

        super().__init__('HTTP %d: %s' % (self.code, message))


class ClientError(HTTPError):

    """Client side error."""


class ServerError(HTTPError):

    """Server side error."""
