from setuptools import setup, find_packages


setup(
    name='httputil',
    packages=find_packages(),
    version='0.3',
    description='Various utilities to work with HTTP',
    license='Public Domain',
    author='Vovan Kuznetsov',
    author_email='vovanec@gmail.com',
    url='https://github.com/vovanec/httputil',
    download_url='https://github.com/vovanec/httputil/tarball/0.3',
    keywords=['http', 'dechunk', 'decompress', 'client'],
    classifiers=[],
    install_requires=['ujson', 'tornado', 'requests'],
)
