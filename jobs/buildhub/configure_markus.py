# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at http://mozilla.org/MPL/2.0/.

import markus
from decouple import config


_configured = False


def get_metrics(namespace):
    global _configured
    if not _configured:
        STATSD_HOST = config('STATSD_HOST', 'localhost')
        STATSD_PORT = config('STATSD_PORT', default=8125)
        STATSD_NAMESPACE = config('STATSD_NAMESPACE', default='')

        # For more options see
        # http://markus.readthedocs.io/en/latest/usage.html#markus-configure
        markus.configure([
            {
                'class': 'markus.backends.datadog.DatadogMetrics',
                'options': {
                    'statsd_host': STATSD_HOST,
                    'statsd_port': STATSD_PORT,
                    'statsd_namespace': STATSD_NAMESPACE,
                }
            }
        ])
        _configured = True

    return markus.get_metrics(namespace)
