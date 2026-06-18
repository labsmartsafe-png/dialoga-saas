import http.server, socketserver, os
class H(http.server.SimpleHTTPRequestHandler):
    pass
port = 5500
os.chdir(os.path.dirname(os.path.abspath(__file__)))
print('Servidor na porta', port)
with socketserver.TCPServer(('', port), H) as s:
    s.serve_forever()
