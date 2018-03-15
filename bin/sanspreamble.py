#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at http://mozilla.org/MPL/2.0/.

import os
import subprocess
import fnmatch


def run():

    exceptions = (
        '.*',
        'docs/conf.py',
        'setup.py',
        'registerServiceWorker.js',
    )

    def is_exception(fp):
        if os.path.basename(fp) in exceptions:
            return True
        for exception in exceptions:
            if fnmatch.fnmatch(fp, exception):
                return True
        return False

    alreadies = subprocess.check_output([
        'git', 'grep',
        'This Source Code Form is subject to the terms of the Mozilla Public'
    ]).decode('utf-8')
    alreadies = [x.split(':')[0] for x in alreadies.splitlines()]

    out = subprocess.check_output(['git', 'ls-files']).decode('utf-8')

    suspect = []
    for fp in out.splitlines():
        if fp in alreadies:
            continue
        if not os.stat(fp).st_size:
            continue
        if is_exception(fp):
            continue
        if True in map(fp.endswith, ('.py', '.js')):
            suspect.append(fp)

    for i, fp in enumerate(suspect):
        if not i:
            print('The following appear to lack a license preamble:'.upper())
        print(fp)

    return len(suspect)


if __name__ == '__main__':
    import sys
    sys.exit(run())
