import socket
import io
import sys
from datetime import datetime
import errno
import os
import signal

class WSGIServer():

    address_family = socket.AF_INET
    socket_type = socket.SOCK_STREAM
    def __init__(self, server_address):
        self.listen_socket = listen_socket = socket.socket(
            self.address_family,
            self.socket_type
        )

        listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listen_socket.bind(server_address)
        listen_socket.listen()
        host, port = listen_socket.getsockname()[:2]
        print(host, port)
        self.server_name = socket.getfqdn(host)
        self.server_port = port
        # Return headers set by framework
        self.headers_set = []
    
    def set_app(self, application):
        self.application = application

    def grim_reaper(self, signum, frame):
        while True:
            try:
                pid, status = os.waitpid(
                    -1,
                    os.WNOHANG
                )
            except OSError:
                return
        
        if pid == 0:
            return

    def serve_forever(self):
        listn_socket = self.listen_socket

        signal.signal(signal.SIGCHLD, self.grim_reaper)
        while True:
            try:
                client_connection, client_address = listn_socket.accept()
            except IOError as e:
                code = e.args
                # Restart 'accept' if it was interrupted
                if code == errno.EINTR:
                    continue
                else:
                    raise
            pid = os.fork()
            if pid == 0: # child
                listn_socket.close()
                self.handle_one_request(client_connection)
                os._exit(0)
            else:   # parent
                client_connection.close()

    def handle_one_request(self, client_connection):
        request_data = client_connection.recv(1024)
        self.request_data = request_data = request_data.decode('utf-8')
        # Print formatted request data
        print(''.join(
            f'< {line}\n' for line in request_data.splitlines()
        ))

        self.parse_request(request_data)
        env = self.get_environ()
        result = self.application(env, self.start_response)
        self.finish_response(result, client_connection)
    
    def parse_request(self, text):
        request_line = text.splitlines()[0]
        request_line = request_line.rstrip(('\r\n'))
        (self.request_method, self.path, self.request_version) = \
            request_line.split()
        if '?' in self.path:
            (self.path, self.query) = self.path.split('?')
        else:
            self.query = ''

    def get_environ(self):
        return {
            # CGI variables
            'REQUEST_METHOD': self.request_method,
            'PATH_INFO': self.path,
            'QUERY_STRING': self.query,
            'SERVER_NAME': self.server_name,
            'SERVER_PORT': self.server_port,
            # WSGI variables
            'wsgi.version': (1, 0),
            'wsgi.url_scheme': 'http',
            'wsgi.input': io.StringIO(self.request_data),
            'wsgi.erros': sys.stderr,
            'wsgi.multithread': False,
            'wsgi.multiprocess': False,
            'wsgi.run_once': False
        }

    def start_response(self, status, response_headers, exc_info=None):
        server_headers = [
            ('Date', datetime.today()),
            ('Server', 'WSGIServer')
        ]
        self.headers_set = [status, response_headers + server_headers]
        return self.finish_response
    
    def finish_response(self, result, client_connection):
        try:
            status, response_headers = self.headers_set
            response = f'HTTP/1.1 {status}\r\n'
            for header in response_headers:
                response += '{0}: {1}\r\n'.format(*header)
            response += '\r\n'
            for data in result:
                response += data.decode('utf-8')
            # Print formatted response
            print(''.join(
                f'> {line}\n' for line in response.splitlines()
            ))
            response_bytes = response.encode()
            client_connection.sendall(response_bytes)
        finally:
            client_connection.close()

SERVER_ADDRESS = (HOST, PORT) = '', 8888

def make_server(server_address, application):
    server = WSGIServer(server_address)
    server.set_app(application)
    return server

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit('Provide a WSGI application object as module:callable')
    app_path = sys.argv[1]
    module, application = app_path.split(':')
    module = __import__(module)
    application = getattr(module, application)
    httpd = make_server(SERVER_ADDRESS, application)
    print(f'WSGIServer: Serving HTTP on port {PORT} ...\n')
    httpd.serve_forever()