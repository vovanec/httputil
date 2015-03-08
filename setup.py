from setuptools import setup, find_packages


install_requires = ['ujson',
                    'tornado',
                    'requests']


tests_require = install_requires + ['vmock',
                                    'nose',
                                    'nosexcover']


setup(
    name='httputil',
    packages=find_packages(),
    version='0.4',
    description='Various utilities to deal with HTTP stuff.',
    author='Vovan Kuznetsov',
    author_email='vovanec@gmail.com',
    maintainer_email='vovanec@gmail.com',
    url='https://github.com/vovanec/httputil',
    download_url='https://github.com/vovanec/httputil/tarball/0.4',
    keywords=['http', 'dechunk', 'decompress', 'client', 'request'],
    license='MIT',
    classifiers=['License :: MIT',
                 'Development Status :: 4 - Beta/Stable',
                 'Intended Audience :: Developers',
                 'Programming Language :: Python :: 3.4'],
    install_requires=install_requires,
    tests_require=tests_require,
    test_suite='nose.collector',
    extras_require={
        'test': tests_require,
    },
)
