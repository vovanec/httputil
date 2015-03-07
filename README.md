# httputil
Utilities for dealing with HTTP data

Example httputil.read_body_stream() usage:
```python

    import httputil

    with open(http_file_path, 'rb') as fh:
        print(b''.join(httputil.read_body_stream(
            fh, chunked=True, compression=httputil.GZIP))
```
