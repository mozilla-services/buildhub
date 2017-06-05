import codecs
import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))


def read_file(filename):
    """Open a related file and return its content."""
    with codecs.open(os.path.join(here, filename), encoding='utf-8') as f:
        content = f.read()
    return content


README = read_file('README.rst')
CHANGELOG = read_file('CHANGELOG.rst')
CONTRIBUTORS = read_file('CONTRIBUTORS.rst')

REQUIREMENTS = [
    "aiohttp",
    "backoff",
    "packaging",
    "kinto-http",
    "kinto-wizard",
]

ENTRY_POINTS = {
    'console_scripts': [
        'scrape_archives = buildhub.scrape_archives:run',
        'sysaddons_updates = buildhub.sysaddons_updates:run',
        'index_filters = buildhub.index_filters:run',
    ],
}


setup(name='buildhub',
      version='0.1.0.dev0',
      description='Buildhub Python libraries.',
      long_description="{}\n\n{}\n\n{}".format(README, CHANGELOG, CONTRIBUTORS),
      license='Apache License (2.0)',
      classifiers=[
          "Programming Language :: Python",
          "Programming Language :: Python :: 3",
          "Programming Language :: Python :: 3.5",
          "Programming Language :: Python :: 3.6",
          "Programming Language :: Python :: Implementation :: CPython",
          "Topic :: Internet :: WWW/HTTP",
          "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
          "License :: OSI Approved :: Apache Software License"
      ],
      author='Mozilla Services',
      author_email='storage-team@mozilla.com',
      url='https://github.com/mozilla-services/buildhub',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=REQUIREMENTS,
      entry_points=ENTRY_POINTS)
