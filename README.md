# httputil
Various useful functions to work with HTTP data

Example httputil.read_body_stream() usage:
```python

    with open(http_file_path, 'rb') as fh:
        print(b''.join(httputil.read_body_stream(
            fh, chunked=True, compression=httputil.GZIP))
```
