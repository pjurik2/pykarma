import threading
import SocketServer
import struct
import wx
import json

import reddit

class ThreadedTCPRequestHandler(SocketServer.BaseRequestHandler):
    def __init__(self, request, client_address, server):
        SocketServer.BaseRequestHandler.__init__(self, request, client_address, server)
        self.root = None
        self.request_answered = False

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
            
        data = json.loads(data)
        try:
            req_id = data['type']
            req_token = data.get('token', -1)
            req_data = data
        except:
            print 'Invalid request'
            return False

        self.request_answered = False
        try:
            handler = self.requests[req_id]
        except:
            handler = self.request_unhandled

        ret = handler(req_data)
        if self.request_answered is False:
            self.respond({'type': req_id, 'success': (ret is not False), 'token': req_token})
        return True

    def request_keywords(self, data):
        data.update({'keywords': self.root.title_stats.keywords(data['title'])})
        self.respond(data)

    def request_linkcheck(self, data):
        title = data.get('title', '')
        url = data.get('url', '')
        
        data.update({'count': self.root.link_check(url, title)})
        self.respond(data)

    def request_linkadd(self, data):   
        source = data['source']
        title = data['title']
        url = data['url']
        subreddit = data['subreddit']
        keywords = data['keywords']
        
        self.root.links_append_safe(source, title, url, subreddit, keywords)
        
        return True

    def request_setkarma(self, data):
        try:
            wx.CallAfter(self.root.set_karma, data['karma'])
            
            return True
        except:
            return False

    def request_getkarma(self, data):
        
        try:
            data.update({'karma': unicode(reddit.get_karma())})
            self.respond(data)
        except:
            return False

    def request_subreddit(self, data):
        data.update({'subreddit': self.root.title_stats.identify(data['title'])})
        self.respond(data)
        return True

    def request_write(self, data):
        self.root.fout.write(data['text'])
        return True

    def request_unhandled(self, data):
        return False

    def respond(self, contents):
        contents = json.dumps(contents)
        
        data = '%s%s' % (struct.pack('L', len(contents)), contents)

        try:
            self.request.sendall(data)
            self.request_answered = True
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
