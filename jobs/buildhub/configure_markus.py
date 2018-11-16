# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at http://mozilla.org/MPL/2.0/.
import os
import time

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

        FILE_METRICS_BASE_DIR = config(
            'MARKUS_FILE_METRICS_BASE_DIR',
            default='/tmp'
        )

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
        elif log_metrics_config == 'cloudwatch':
            markus.configure([
                {
                    'class': 'markus.backends.cloudwatch.CloudwatchMetrics',
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
        elif log_metrics_config == 'file':
            markus.configure([
                {
                    'class': 'buildhub.configure_markus.FileMetrics',
                    'options': {
                        'base_dir': FILE_METRICS_BASE_DIR,
                    }
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


class FileMetrics(BackendBase):
    """Use when you want to write the metrics to files.

        markus.configure([
            {
                'class': 'buildhub.configure_markus.FileMetrics',
                'options': {
                    'base_dir': '/my/log/path'
                }
            }
        ])
    """

    def __init__(self, options):
        self.prefix = options.get("prefix", "")
        self.base_dir = options.get("base_dir", os.path.abspath("."))
        self.fns = set()
        os.makedirs(self.base_dir, exist_ok=True)

    def _log(self, metrics_kind, stat, value, tags):
        tags = ("#%s" % ",".join(tags)) if tags else ""
        fn = os.path.join(self.base_dir, "{}.{}.log".format(stat, metrics_kind))
        with open(fn, "a") as f:
            print("{:.3f}\t{}{}".format(time.time(), value, tags), file=f)
        if fn not in self.fns:
            print("Wrote first-time metrics in {}".format(fn))
            self.fns.add(fn)

    def incr(self, stat, value=1, tags=None):
        """Increment a counter"""
        self._log("count", stat, value, tags)

    def gauge(self, stat, value, tags=None):
        """Set a gauge"""
        self._log("gauge", stat, value, tags)

    def timing(self, stat, value, tags=None):
        """Set a timing"""
        self._log("timing", stat, value, tags)

    def histogram(self, stat, value, tags=None):
        """Set a histogram"""
        self._log("histogram", stat, value, tags)
