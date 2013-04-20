import struct
import socket
import socks

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
        return self.request('write', text)

    def subreddit(self, title):
        return self.request('subreddit', title)

    def keywords(self, title):
        return self.request('keywords', title)

    def setkarma(self, karma):
        try:
            return self.request('setkarma', unicode(karma))
        except:
            return 'SE'

    def linkcheck(self, url, title):
        ret = self.request('linkcheck', self.implode(url, title))
        try:
            return int(ret)
        except:
            return 'SE'

    def getkarma(self):
        ret = self.request('getkarma', u'')
        try:
            return int(ret)
        except:
            return 'SE'

    def linkadd(self, source, title, url, subreddit, keywords=''):
        return self.request('linkadd', self.implode(source, title, url, subreddit, keywords))

    def implode(self, *args):
        args_fixed = [arg.replace('/', '//') for arg in args]

        data = '{/}'.join(args_fixed)
        return data


    def request(self, ident, contents):
        data = '%s%s\0%s\0' % (struct.pack('L', len(ident.encode('utf-8'))+len(contents.encode('utf-8'))+2),
                               ident.encode('utf-8'),
                               contents.encode('utf-8'))

        self.sock.sendall(data)


        length_str = self.sock.recv(4)
        length = struct.unpack('L', length_str)[0]
        data = ''
        while len(data) != length:
            new_data = self.sock.recv(length - len(data))
            if len(new_data) == 0:
                break

            data += new_data

        return data.decode('utf-8')

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
