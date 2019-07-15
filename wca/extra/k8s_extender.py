import http.server
import json
import logging
import socketserver
from typing import Dict, List

from dataclasses import dataclass

log = logging.getLogger(__name__)

_PROMETHEUS_QUERY_PATH = "/api/v1/query"
_PROMETHEUS_QUERY_RANGE_PATH = "/api/v1/query_range"
_PROMETHEUS_URL_TPL = '{prometheus}{path}?query={name}'
_PROMETHEUS_TIME_TPL = '&start={start}&end={end}&step=1s'
_PROMETHEUS_TAG_TPL = '{key}="{value}"'

def _build_prometheus_url(prometheus, name, tags=None, window_size=None, event_time=None):
    tags = tags or dict()
    path = _PROMETHEUS_QUERY_PATH
    time_range = ''

    # Some variables need to be overwritten for range queries.
    if window_size and event_time:
        offset = window_size / 2
        time_range = _PROMETHEUS_TIME_TPL.format(
            start=event_time - offset,
            end=event_time + offset)
        path = _PROMETHEUS_QUERY_RANGE_PATH

    url = _PROMETHEUS_URL_TPL.format(
        prometheus=prometheus,
        path=path,
        name=name,
    )

    # Prepare additional tags for query.
    query_tags = []
    for k, v in tags.items():
        query_tags.append(_PROMETHEUS_TAG_TPL.format(key=k, value=v))
    query_tags_str = ','.join(query_tags)

    # Build final URL from all the components.
    url = ''.join([url, "{", query_tags_str, "}", time_range])

    return url


@dataclass
class ExtenderArgs:
    Nodes: List[Dict]
    Pod: dict
    NodeNames: List[str]


# ExtenderFilterResult represents the results of a filter call to an extender
@dataclass
class ExtenderFilterResult:
    NodeNames: List[str]
    # Filtered out nodes where the pod can't be scheduled and the failure messages
    FailedNodes: Dict[str, str]
    # Error message indicating failure
    Error: str


class K8SHandler(http.server.BaseHTTPRequestHandler):

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        args = json.loads(self.rfile.read(content_length).decode())
        extender_args = ExtenderArgs(**args)

        if self.path == "/api/scheduler/filter":
            result_simple = self._filter(extender_args)
        elif self.path == "/api/scheduler/prioritize":
            result_simple = self._prioritize(extender_args)
        else:
            self.send_response(404)
            self.end_headers()
            return

        self.send_response(200)
        self.end_headers()

        result_as_json = json.dumps(result_simple).encode()
        log.info('%s %s', self.path, result_as_json)
        self.wfile.write(result_as_json)

    def _filter(self, extender_args):
        return dict(
            NodeNames=[extender_args.NodeNames[0]],
            # NodeNames=extender_args.NodeNames,
            # NodeNames=[],
            FailedNodes={},
            Error='',
        )

    def _prioritize(self, extender_args: ExtenderArgs):
        nodes = []
        for score, nodename in enumerate(extender_args.NodeNames):
            nodes.append(
                dict(Host=nodename, Score=0)
            )
        return nodes


class ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True


def start_server(port):
    with http.server.HTTPServer(('', port), K8SHandler) as httpd:
        log.info('serving at port: %s', port)
        httpd.serve_forever()

# STATE of cluster and latest characteristics of the apps
app_stats = {}
node_stats = {}

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    start_server(12345)
