import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Tuple, List

from rmi import storage
from rmi.metrics import Metric
from wrapper.parser import parse_loop

log = logging.getLogger(__name__)


def create_message(metrics: List[Metric]) -> Tuple[int, str]:
    """
    checks whether the metrics are convertible to
    the prometheus format, if so does the conversion and returns code and encoded response body.
    """
    is_convertible, err = storage.is_convertable_to_prometheus_exposition_format(metrics)
    if not metrics:
        response_code = 204
        body = "".encode('utf-8')
    elif is_convertible:
        response_code = 200
        body = storage.convert_to_prometheus_exposition_format(metrics).encode('utf-8')
    else:
        response_code = 500
        body = err.encode('utf-8')
    log.debug("Message return code: {0}\n body: {1}".format(response_code, body))
    return response_code, body


class MetricsRequestHandler(BaseHTTPRequestHandler):
    def __init__(self, request, client_address, server):
        super().__init__(request, client_address, server)

    def do_GET(self):
        # pass metrics list as a copy, as it is modified in a separate thread
        response_code, body = create_message(parse_loop.metrics.copy())
        self.send_response(response_code)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(body)


def run_server(ip: str, port: int) -> None:
    log.debug("Starting HTTP server at {0}:{1}".format(ip, port))
    httpd = HTTPServer((ip, port), MetricsRequestHandler)
    httpd.serve_forever()
