import http.server
import json
import logging
import socketserver
from typing import Dict, List

import requests
from dataclasses import dataclass

log = logging.getLogger(__name__)

# PUBLIC CONFIG
PORT = 12345
PROMETHEUS = 'http://100.64.176.36:9090'
NAMESPACE = 'default'
LEVEL = logging.INFO
FIT_MODE = "rsswss"

# CONSTANTS
_PROMETHEUS_QUERY_PATH = "/api/v1/query"
_PROMETHEUS_QUERY_RANGE_PATH = "/api/v1/query_range"
_PROMETHEUS_URL_TPL = '{prometheus}{path}?query={name}'
_PROMETHEUS_TIME_TPL = '&start={start}&end={end}&step=1s'
_PROMETHEUS_TAG_TPL = '{key}="{value}"'


def _build_raw_query(prometheus, query):
    path = _PROMETHEUS_QUERY_PATH
    url = _PROMETHEUS_URL_TPL.format(
        prometheus=prometheus,
        path=path,
        name=query,
    )
    return url


def _build_prometheus_url(prometheus, name, tags=None, start=None, end=None):
    tags = tags or dict()

    # Some variables need to be overwritten for range queries.
    if start and end:
        path = _PROMETHEUS_QUERY_RANGE_PATH
        time_range = _PROMETHEUS_TIME_TPL.format(start=start, end=end)
    else:
        path = _PROMETHEUS_QUERY_PATH
        time_range = ''

    url_and_query_without_tags = _PROMETHEUS_URL_TPL.format(
        prometheus=prometheus,
        path=path,
        name=name,
    )

    # Build final URL from all the components.
    if tags:
        # Prepare additional tags for query.
        query_tags = []
        for k, v in tags.items():
            query_tags.append(_PROMETHEUS_TAG_TPL.format(key=k, value=v))
        query_tags_str = ','.join(query_tags)
        url = ''.join([url_and_query_without_tags, "{", query_tags_str, "}", time_range])
    else:
        url = ''.join([url_and_query_without_tags, time_range])

    return url


def do_query(name, result_tag, tags=None):
    url = _build_prometheus_url(PROMETHEUS, name, tags)
    response = requests.get(url)
    response = response.json()
    if response['status'] == 'error':
        raise Exception(response['error'])
    assert response['data']['resultType'] == 'vector'
    result = response['data']['result']
    return {pair['metric'][result_tag]: float(pair['value'][1]) for pair in result}


def do_raw_query(query, result_tag):
    url = _build_raw_query(PROMETHEUS, query)
    response = requests.get(url)
    response = response.json()
    if response['status'] == 'error':
        raise Exception(response['error'])
    assert response['data']['resultType'] == 'vector'
    result = response['data']['result']
    return {pair['metric'][result_tag]: float(pair['value'][1]) for pair in result}


def _filter_logic(app, nodes, namespace):
    return nodes


PRIORITY_QUERY = 'fit_avg{app="%s"}'

def _prioritize_logic(app, nodes, namespace):
    if namespace != NAMESPACE:
        log.info('ignoring pods not from %r namespace (got %r)', NAMESPACE, namespace)
        return {}

    # Get most fitted nodes.
    priorities = {}
    query = PRIORITY_QUERY %(app)
    nodes_fit = do_raw_query(query, 'node')
    log.info('nodes_fit for %r: %r', app, nodes_fit)
    for node in nodes:
        priorities[node] = int(nodes_fit.get(node, 0) * 100)
    return priorities


@dataclass
class ExtenderArgs:
    Nodes: List[Dict]
    Pod: dict
    NodeNames: List[str]


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
        log.debug('%s %s', self.path, result_as_json)
        self.wfile.write(result_as_json)

    def log_request(self, code='-', size='-'):
        pass

    def _extract_common_input(self, extender_args):
        """ :returns app, nodes, namespace"""
        nodes = extender_args.NodeNames
        labels = extender_args.Pod['metadata']['labels']
        # generic input
        namespace = extender_args.Pod['metadata']['namespace']
        # specific workloads input
        app = labels.get('app', None)
        return app, nodes, namespace

    def _filter(self, extender_args):
        # Logic
        log.debug('Pod: \n%s:', json.dumps(extender_args.Pod, indent=4))
        app, nodes, namespace = self._extract_common_input(extender_args)
        self._extract_common_input(extender_args)
        nodes = _filter_logic(app, nodes, namespace)
        log.info('filtered = %s', ', '.join(nodes))
        # Encode
        return dict(
            NodeNames=nodes,
            FailedNodes={},
            Error='',
        )

    def _prioritize(self, extender_args: ExtenderArgs):
        # Logic
        app, nodes, namespace = self._extract_common_input(extender_args)
        priorities = _prioritize_logic(app, nodes, namespace)
        log.info('priorities: %r', priorities)
        # Encode as PriorityList
        priority_list = [dict(Host=node, Score=priorities.get(node, 0)) for node in nodes]
        log.debug('priority list = %s', ', '.join('%s=%s' % (d['Host'], d['Score']) for d in
                                                  sorted(priority_list, key=lambda d: d['Host'])))
        return priority_list


class ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True


def main(level, port):
    logging.basicConfig(level=level)
    with http.server.HTTPServer(('', port), K8SHandler) as httpd:
        log.info('serving at port: %s', port)
        httpd.serve_forever()


if __name__ == '__main__':
    main(LEVEL, PORT)
