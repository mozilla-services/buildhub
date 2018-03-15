# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at http://mozilla.org/MPL/2.0/.

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

ENTRY_POINTS = {
    'console_scripts': [
        'to-kinto = buildhub.to_kinto:run',
        'inventory-to-records = buildhub.inventory_to_records:run',
        'latest-inventory-to-kinto = buildhub.lambda_s3_inventory:lambda_handler',
    ],
}


setup(name='buildhub',
      version='1.1.5',
      description='Buildhub Python libraries.',
      long_description="{}\n\n{}\n\n{}".format(README, CHANGELOG, CONTRIBUTORS),
      license='MPL 2.0',
      classifiers=[
          "Programming Language :: Python",
          "Programming Language :: Python :: 3",
          "Programming Language :: Python :: 3.5",
          "Programming Language :: Python :: 3.6",
          "Programming Language :: Python :: Implementation :: CPython",
          "Topic :: Internet :: WWW/HTTP",
          "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
          "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)",
      ],
      author='Mozilla Services',
      author_email='storage-team@mozilla.com',
      url='https://github.com/mozilla-services/buildhub',
      packages=find_packages(),
      package_dir={'buildhub': 'buildhub'},
      package_data={'buildhub': ['initialization.yml']},
      include_package_data=True,
      zip_safe=False,
      # Use
      #  `pip -r requirements/default.txt -c requirements/constraints.txt`
      # instead.
      install_requires=[],
      entry_points=ENTRY_POINTS)
