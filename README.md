# httputil
Various useful functions to work with HTTP data

Example httputil.read_body_stream() usage:
```python

    with open(file_path, 'rb') as fh:
        print(b''.join(httputil.read_body_stream(
            fh, chunked=chunked, compression=compression))
```
