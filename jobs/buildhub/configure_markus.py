# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at http://mozilla.org/MPL/2.0/.

import markus
from markus.backends import BackendBase
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
        log_metrics_config = config('LOG_METRICS', default='datadog')
        if log_metrics_config == 'logging':
            markus.configure([
                {
                    'class': 'markus.backends.logging.LoggingMetrics',
                    'options': {
                        'logger_name': 'metrics'
                    }
                }
            ])
        elif log_metrics_config == 'datadog':
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
        elif log_metrics_config == 'void':
            markus.configure([
                {
                    'class': 'buildhub.configure_markus.VoidMetrics',
                }
            ])
        else:
            raise NotImplementedError(
                f'Unrecognized LOG_METRICS value {log_metrics_config}'
            )
        _configured = True

    return markus.get_metrics(namespace)


class VoidMetrics(BackendBase):
    """Use when you want nothing with the markus metrics. E.g.

        markus.configure([
            {
                'class': 'buildhub.configure_markus.VoidMetrics',
            }
        ])
    """

    def incr(self, stat, value, tags=None):
        pass

    def gauge(self, stat, value, tags=None):
        pass

    def timing(self, stat, value, tags=None):
        pass

    def histogram(self, stat, value, tags=None):
        pass
