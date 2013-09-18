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
        self.req_answered = False

    def handle(self):
        self.requests = {'gui.write': self.req_gui_write,
                         'gui.karma_set': self.req_gui_karma_set,
                         'gui.karma_get': self.req_gui_karma_get,
                         'gui.link_add': self.req_gui_link_add,
                         'reddit.get_title_subreddit': self.req_get_title_subreddit,
                         'reddit.get_title_keywords': self.req_get_title_keywords,
                         'reddit.get_link_posted_count': self.req_get_link_posted_count
                         }

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

        self.req_answered = False
        try:
            handler = self.requests[req_id]
        except:
            handler = self.req_unhandled

        ret = handler(req_data)
        if self.req_answered is False:
            self.respond({'type': req_id, 'success': (ret is not False), 'token': req_token})
        return True

    def req_gui_write(self, data):
        self.root.fout.write(data['text'])
        return True
        
    def req_gui_link_add(self, data):   
        source = data['source']
        title = data['title']
        url = data['url']
        subreddit = data['subreddit']
        keywords = data['keywords']
        
        self.root.links_append_safe(source, title, url, subreddit, keywords)
        
        return True

    def req_gui_karma_set(self, data):
        try:
            wx.CallAfter(self.root.set_karma, data['karma'])
            
            return True
        except:
            return False

    def req_gui_karma_get(self, data):
        
        try:
            data.update({'karma': unicode(reddit.get_karma())})
            self.respond(data)
        except:
            return False
        
    def req_get_title_keywords(self, data):
        data.update({'keywords': self.root.title_stats.keywords(data['title'])})
        self.respond(data)

    def req_get_link_posted_count(self, data):
        title = data.get('title', '')
        url = data.get('url', '')
        
        data.update({'count': self.root.get_link_posted_count(url, title)})
        self.respond(data)

    def req_get_title_subreddit(self, data):
        data.update({'subreddit': self.root.title_stats.identify(data['title'])})
        self.respond(data)
        return True

    def req_unhandled(self, data):
        return False

    def respond(self, contents):
        contents = json.dumps(contents)
        
        data = '%s%s' % (struct.pack('L', len(contents)), contents)

        try:
            self.request.sendall(data)
            self.req_answered = True
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
