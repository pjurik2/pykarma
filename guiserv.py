import threading
import SocketServer
import struct
import wx

import reddit

class ThreadedTCPRequestHandler(SocketServer.BaseRequestHandler):
    def __init__(self, request, client_address, server):
        SocketServer.BaseRequestHandler.__init__(self, request, client_address, server)
        self.root = None

    def handle(self):
        self.requests = {'write': self.request_write,
                         'subreddit': self.request_subreddit,
                         'setkarma': self.request_setkarma,
                         'getkarma': self.request_getkarma,
                         'linkcheck': self.request_linkcheck,
                         'linkadd': self.request_linkadd,
                         'keywords': self.request_keywords}

        while self.handle_request():
            pass

    def handle_request(self):
        try:
            length_str = self.request.recv(4)
        except:
            return False
        if len(length_str) == 0:
            return False
        length = struct.unpack('L', length_str)[0]

        data = ''
        new_data = ''
        while len(data) != length:
            try:
                new_data = self.request.recv(length - len(data))
            except:
                break
            if len(new_data) == 0:
                break

            data += new_data

        if length > 0 and new_data == '':
            return False
            
        try:
            req_id, req_data = data.split('\0', 2)[:2]
            req_id = req_id.decode('utf-8')
            req_data = req_data.decode('utf-8')
        except:
            print 'Invalid request'
            return False

        
        try:
            handler = self.requests[req_id]
        except:
            handler = self.request_unhandled

        handler(req_data)
        return True
            
    def explode(self, data):
        args = data.split('{/}')
        args_fixed = [arg.replace('//', '/') for arg in args]

        return args_fixed

    def request_keywords(self, title):
        self.respond(self.root.title_stats.keywords(title))

    def request_linkcheck(self, data):
        ret = unicode(self.root.link_check(*self.explode(data)))
        self.respond(ret)

    def request_linkadd(self, args):
        self.root.links_append_safe(*self.explode(args))
        self.respond('OK')

    def request_setkarma(self, karma):
        try:
            wx.CallAfter(self.root.set_karma, karma)
            self.respond('OK')
        except:
            self.respond('ER')

    def request_getkarma(self, etc):
        try:
            self.respond(unicode(reddit.get_karma()))
        except:
            self.respond('ER')

    def request_subreddit(self, title):
        self.respond(self.root.title_stats.identify(title))

    def request_write(self, text):
        self.root.fout.write(text)
        self.respond('OK')

    def request_unhandled(self, data):
        self.respond('ER')

    def respond(self, contents):
        data = '%s%s' % (struct.pack('L', len(contents.encode('utf-8'))),
                         contents.encode('utf-8'))

        try:
            self.request.sendall(data)
        except:
            print 'Client socket request error'

class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    def set_root(self, root):
        self.root = root

class GUIServer:
    def __init__(self, root, host, port):
        self.root = root
        self.host = host
        self.port = port
        ThreadedTCPRequestHandler.root = root

    def serve(self):
        self.server = ThreadedTCPServer((self.host, self.port), ThreadedTCPRequestHandler)

        self.server_thread = threading.Thread(target=self.server.serve_forever)

        self.server_thread.daemon = True
        self.server_thread.start()

    def stop(self):
        self.server.shutdown()
            
if __name__ == "__main__":
    HOST, PORT = "localhost", 9367

    s = GUIServer(None, HOST, PORT)
    s.serve()
