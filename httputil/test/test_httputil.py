"""Unit test for httputil module.
"""

__author__ = 'vovanec@gmail.com'


import inspect
import os
import unittest

import httputil


MY_DIR = os.path.dirname(os.path.abspath(
                         inspect.getsourcefile(inspect.currentframe())))


CONTENT_FILES = [
    ('bzipped', False, httputil.BZIP2),
    ('chunked_deflate', True, httputil.DEFLATE),
    ('chunked_gzipped', True, httputil.GZIP),
    ('chunked', True, None),
    ('deflate', False, httputil.DEFLATE),
    ('gzipped', False, httputil.GZIP)
]


class TestHTTPUtil(unittest.TestCase):

    def test_read_body_stream(self):

        for fname, chunked, compression in CONTENT_FILES:
            file_path = os.path.join(MY_DIR, 'http_content', fname)
            with self.subTest(fname):
                with open(file_path, 'rb') as fh:
                    with open(file_path + '.expected', 'rb') as exp_fh:
                        content = b''.join(httputil.read_body_stream(
                            fh, chunked=chunked, compression=compression))
                        self.assertEqual(content, exp_fh.read())

    def test_read_plain_stream(self):

        file_path = os.path.join(MY_DIR, 'http_content', 'bzipped.expected')
        with open(file_path, 'rb') as fh:
            expected_content = fh.read()

        with open(file_path, 'rb') as fh:
            content = b''.join(httputil.read_body_stream(
                fh, chunked=False, compression=None))
            self.assertEqual(expected_content, content)


if __name__ == '__main__':
    unittest.main()
