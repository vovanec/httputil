# httputil
Utilities for dealing with HTTP data

Example httputil.read_body_stream() usage:
```python

    import httputil

    with open(http_file_path, 'rb') as fh:
        print(b''.join(httputil.read_body_stream(
            fh, chunked=True, compression=httputil.GZIP))
```

Example request engines use to implement API clients:
```python

    from httputil.request_engine import async_engine
    from httputil.request_engine import sync_engine
    from httputil.request_engine import errors
    
    log = logging.getLogger('http_client')

    DEF_REQUEST_TIMEOUT = 10
    DEF_CONNECT_TIMEOUT = 3
    DEF_NUM_RETRIES = 3
    
    API_BASE_URL = 'http://echo.jsontest.com'
    ECHO_URL = '/key/value/one/two'
    
    
    class SyncAPIClient(object):
    
        def __init__(self, connect_timeout=DEF_CONNECT_TIMEOUT,
                     request_timeout=DEF_REQUEST_TIMEOUT,
                     connection_retries=DEF_NUM_RETRIES):
    
            """Constructor.
            """
    
            self._engine = sync_engine.SyncRequestEngine(
                API_BASE_URL, connect_timeout, request_timeout, connection_retries)
    
        def echo(self):
    
            return self._engine.request(ECHO_URL)
    
    
    class AsyncAPIClient(object):
    
        def __init__(self, connect_timeout=DEF_CONNECT_TIMEOUT,
                     request_timeout=DEF_REQUEST_TIMEOUT,
                     connection_retries=DEF_NUM_RETRIES):
    
            """Constructor.
            """
    
            self._engine = async_engine.AsyncRequestEngine(
                API_BASE_URL, connect_timeout, request_timeout, connection_retries)
    
        def echo(self, callback=None):
    
            return self._engine.request(ECHO_URL, callback=callback)
    
    
    @gen.coroutine
    def example_async_client(api_client):
        """Example async client use with coroutines.
        """
    
        try:
            pprint((yield from api_client.echo()))
        except errors.APIError as exc:
            log.exception('Exception occurred: %s', exc)
    
        yield gen.Task(lambda *args, **kwargs: ioloop.IOLoop.current().stop())
    
    
    def example_async_client_with_cb(api_client):
        """Example async client use with callbacks.
        """
    
        api_client.echo(callback=pprint)
    
    
    def example_sync_client(api_client):
        """Example sync client use with.
        """
    
        try:
            pprint(api_client.echo())
        except errors.APIError as exc:
            log.exception('Exception occurred: %s', exc)


    def main():
        """Run the examples.
        """
    
        logging.basicConfig(level=logging.INFO)
    
        example_sync_client(SyncAPIClient())
        example_async_client_with_cb(AsyncAPIClient())
        example_async_client(AsyncAPIClient())
    
        io_loop = ioloop.IOLoop.current()
        io_loop.start()


if __name__ == '__main__':
    main()
```