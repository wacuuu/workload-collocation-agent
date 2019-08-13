# Copyright (c) 2019 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import http
import logging
import socketserver
import threading
from typing import Optional

log = logging.getLogger(__name__)

from dataclasses import dataclass
import http.server

from wca.storage import Storage, is_convertable_to_prometheus_exposition_format, \
    InconvertibleToPrometheusExpositionFormat, convert_to_prometheus_exposition_format


class ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True


@dataclass
class HTTPStorage(Storage):
    port: int = 9100

    def __post_init__(self):
        self._message_counter = 0
        self._output = ''
        self._merged_output = ''

        class MetricHandler(http.server.BaseHTTPRequestHandler):

            def log_request(self, code='-', size='-'):
                log.debug('%s %s %s', self.requestline, code, size)

            def do_GET(self2):
                self2.send_response(200)
                self2.end_headers()
                self2.wfile.write(self._output.encode())

        def start_server():
            with http.server.HTTPServer(('', self.port), MetricHandler) as httpd:
                log.info('serving at port: %s', self.port)
                httpd.serve_forever()

        threading.Thread(target=start_server, daemon=True).start()

    def store(self, metrics):
        self._message_counter += 1
        is_convertable, error_message = is_convertable_to_prometheus_exposition_format(metrics)
        if not is_convertable:
            log.error(
                'failed to convert metrics into '
                'prometheus exposition format; error: "{}"'.format(error_message)
            )
            raise InconvertibleToPrometheusExpositionFormat(error_message)
        else:
            msg = convert_to_prometheus_exposition_format(metrics, None, None)
            self._output = msg
