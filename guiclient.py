import struct
import socket
import socks
import json

import out

class GUIClient():
    def __init__(self, port, ip='localhost'):
        self.port = port
        self.ip = ip
        self.sock = None

    def connect(self):
        socks.setdefaultproxy()
        self.sock = socket.socket()
        self.sock.connect((self.ip, self.port))

    def write(self, text):
        return self.request('write', {'text': text})

    def subreddit(self, title):
        return self.request('subreddit', {'title': title})['subreddit']

    def keywords(self, title):
        return self.request('keywords', {'title': title})['keywords']

    def setkarma(self, karma):
        return self.request('setkarma', {'karma': karma})

    def linkcheck(self, url, title):
        ret = self.request('linkcheck', {'url': url, 'title': title})
        return ret['count']

    def getkarma(self):
        ret = self.request('getkarma')
        return ret['karma']

    def linkadd(self, source, title, url, subreddit, keywords=''):
        req = {'source': source,
               'title': title,
               'url': url,
               'subreddit': subreddit,
               'keywords': keywords}
               
        return self.request('linkadd', req)

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
    print rpc.subreddit('Black March begins today - hit RIAA & MPAA where it hurts')
    print 'Exiting...'
