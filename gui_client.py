import struct
import socket
import json

import out

class GUIClient():
    def __init__(self, port, ip='localhost'):
        self.port = port
        self.ip = ip
        self.sock = None
        self.write = self.gui_write

    def connect(self):
        self.sock = socket.socket()
        self.sock.connect((self.ip, self.port))

    def gui_write(self, text):
        return self.request('gui.write', {'text': text})
        
    def gui_karma_set(self, karma):
        return self.request('gui.karma_set', {'karma': karma})
        
    def gui_karma_get(self):
        return self.request('gui.karma_get')['karma']

    def gui_link_add(self, source, title, url, subreddit, keywords='', **kwargs):
        req = kwargs
        req.update({'source': source,
               'title': title,
               'url': url,
               'subreddit': subreddit,
               'keywords': keywords})
               
        return self.request('gui.link_add', req)

    def get_title_subreddit(self, title):
        return self.request('reddit.get_title_subreddit', {'title': title})['subreddit']

    def get_title_keywords(self, title):
        return self.request('reddit.get_title_keywords', {'title': title})['keywords']

    def get_link_posted_count(self, url, title=''):
        ret = self.request('reddit.get_link_posted_count', {'url': url, 'title': title})
        return ret['count']
        
    def get_learned_stats(self, title, keywords=None):
        ret = self.request('reddit.get_learned_stats', {'keywords': keywords, 'title': title})
        return ret

    def request(self, ident, contents=None):
        self.send(ident, contents)
        return self.recv()
    
    def send(self, ident, contents=None):
        if contents is None:
            contents = {}
            
        contents['type'] = ident
        contents = json.dumps(contents)
        data = '%s%s' % (struct.pack('L', len(contents)),
                         contents)

        self.sock.sendall(data)

    def recv(self):
        length_str = self.sock.recv(4)
        length = struct.unpack('L', length_str)[0]
        data = ''
        while len(data) != length:
            new_data = self.sock.recv(length - len(data))
            if len(new_data) == 0:
                break

            data += new_data

        return json.loads(data)

def new_rpc(name='Client'):
    s = GUIClient(9367)
    s.connect()
    out.set_output(name, s)
    return s

if __name__ == '__main__':
    print 'Starting RPC...'
    rpc = new_rpc()
    print 'RPC started.'
    print rpc.get_title_subreddit('Black March begins today - hit RIAA & MPAA where it hurts')
    print 'Exiting...'
