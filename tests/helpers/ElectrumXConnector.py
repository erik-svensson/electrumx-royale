import json
import logging, socket, ssl
import time

from tests.helpers.authproxy import JSONRPCException


class Connector:

    def __init__(self, host, port, ssl=False, timeout=5, network='mainnet'):
        self.log.log(15, "Starting...")
        self.host = host
        self.port = port
        self.ssl = ssl
        self.timeout = timeout
        self.network = network

        self.connection = None
        self._connect()

    def _connect(self):
        self.log.log(10, "_connect {} {}".format(self.host, self.port))
        self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connection.settimeout(self.timeout)
        if self.ssl:
            self.connection = ssl.wrap_socket(self.connection)
        self.connection.connect((self.host, self.port))


class ElectrumXConnector(Connector):

    def __init__(self, *args, **kwargs):
        self.log = logging.getLogger(type(self).__name__)
        super(type(self), self).__init__(*args, **kwargs)

    def _receive(self):
        raw = bytearray()
        while raw[-1:] != b'\n':
            chunk = self.connection.recv(1024)
            raw.extend(chunk)
        r = json.loads(raw)
        self.log.log(5, "_receive {}".format(r))
        return raw

    def send(self, method, *args):
        payload = json.dumps(
            {
                "jsonrpc": "2.0",
                "id": int(time.time()*1000),
                "method": method,
                "params": args
            }
        ) + '\n'
        payload = payload.encode()
        self.log.log(5, "send {} {}".format(method, args))
        self.connection.send(payload)

        response = json.loads(self._receive())

        if response.get('error') is not None:
            raise JSONRPCException(response['error'])
        elif 'result' not in response:
            raise JSONRPCException({
                'code': -343, 'message': 'missing JSON-RPC result'})

        return response['result']
