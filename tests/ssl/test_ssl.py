import pytest
import requests
import ssl
import time
from multiprocessing import Process
from wca.security import HTTPSAdapter
from flask import Flask


def run_simple_https_server(ssl_context: ssl.SSLContext):
    server = Flask('Simple test server')

    @server.route('/test')
    def test():
        return 'Passed'

    server.run(host='127.0.0.1', port=8080, ssl_context=ssl_context)


def test_good_certificate():
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    ssl_context.load_cert_chain('tests/ssl/goodkey.crt', 'tests/ssl/goodkey.key')
    server = Process(target=run_simple_https_server, args=(ssl_context,))
    server.start()
    time.sleep(0.5)
    try:
        s = requests.Session()
        s.mount('https://localhost:8080/', HTTPSAdapter())
        r = s.get('https://localhost:8080/test', verify='tests/ssl/rootCA.crt')
        assert r.text == 'Passed'
        server.terminate()
    except Exception:
        server.terminate()
        raise


def test_wrong_certificate():
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    ssl_context.load_cert_chain('tests/ssl/goodkey.crt', 'tests/ssl/goodkey.key')
    server = Process(target=run_simple_https_server, args=(ssl_context,))
    server.start()
    time.sleep(0.5)
    with pytest.raises(requests.exceptions.SSLError):
        s = requests.Session()
        try:
            s.mount('https://localhost:8080/', HTTPSAdapter())
            s.get('https://localhost:8080/test', verify='tests/ssl/wrongRootCA.crt')
            server.terminate()
        except Exception:
            server.terminate()
            raise


def test_unsupported_rsa_1024():
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    ssl_context.load_cert_chain('tests/ssl/rsa1024.crt', 'tests/ssl/rsa1024.key')
    server = Process(target=run_simple_https_server, args=(ssl_context,))
    server.start()
    time.sleep(0.5)
    with pytest.raises(requests.exceptions.SSLError):
        s = requests.Session()
        try:
            s.mount('https://localhost:8080/', HTTPSAdapter())
            s.get('https://localhost:8080/test', verify='tests/ssl/rootCA.crt')
            server.terminate()
        except Exception:
            server.terminate()
            raise


def test_supported_rsa_2048():
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    ssl_context.load_cert_chain('tests/ssl/rsa2048.crt', 'tests/ssl/rsa2048.key')
    server = Process(target=run_simple_https_server, args=(ssl_context,))
    server.start()
    time.sleep(0.5)
    with pytest.raises(requests.exceptions.SSLError):
        s = requests.Session()
        try:
            s.mount('https://localhost:8080/', HTTPSAdapter())
            s.get('https://localhost:8080/test', verify='tests/ssl/rootCA.crt')
            server.terminate()
        except Exception:
            server.terminate()
            raise


def test_supported_tls_1_2():
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    ssl_context.load_cert_chain('tests/ssl/goodkey.crt', 'tests/ssl/goodkey.key')
    server = Process(target=run_simple_https_server, args=(ssl_context,))
    server.start()
    time.sleep(0.5)
    try:
        s = requests.Session()
        s.mount('https://localhost:8080/', HTTPSAdapter())
        r = s.get('https://localhost:8080/test', verify='tests/ssl/rootCA.crt')
        assert r.text == 'Passed'
        server.terminate()
    except Exception:
        server.terminate()
        raise


def test_unsupported_tls_1_1():
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_1)
    ssl_context.load_cert_chain('tests/ssl/goodkey.crt', 'tests/ssl/goodkey.key')
    server = Process(target=run_simple_https_server, args=(ssl_context,))
    server.start()
    time.sleep(0.5)
    with pytest.raises(requests.exceptions.SSLError):
        s = requests.Session()
        try:
            s.mount('https://localhost:8080/', HTTPSAdapter())
            s.get('https://localhost:8080/test', verify='tests/ssl/rootCA.crt')
            server.terminate()
        except Exception:
            server.terminate()
            raise


def test_unsupported_tls_1_0():
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
    ssl_context.load_cert_chain('tests/ssl/goodkey.crt', 'tests/ssl/goodkey.key')
    server = Process(target=run_simple_https_server, args=(ssl_context,))
    server.start()
    time.sleep(0.5)
    with pytest.raises(requests.exceptions.SSLError):
        s = requests.Session()
        try:
            s.mount('https://localhost:8080/', HTTPSAdapter())
            s.get('https://localhost:8080/test', verify='tests/ssl/rootCA.crt')
            server.terminate()
        except Exception:
            server.terminate()
            raise
