# -*- coding: cp1252 -*-
#import socks
#import socket
##socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, "127.0.0.1", 8080)
##socket.socket = socks.socksocket

import time
import threading
import re
import urllib2
import urllib

import xmlparse

from repl import *

endswith = repl_load('filters/tfendswith.txt')
startswith = repl_load('filters/tfstartswith.txt')
ratelimit = [('reddit.com', 3.5)]
threadlimit = [('reddit.com', 1)]
lastvisit = {}
lvlock = threading.Lock()
outstanding = {}

title_strip = u'\r\n\t -:«»||•—'

def title_parse(title, url=''):
    global startswith, endswith, title_strip
    
    title = xmlparse.unescape(title).strip().strip(title_strip)
    title = re.sub(u'\s+', u' ', title, flags=re.UNICODE)

    for urlpart, pattern in startswith:
        if (urlpart in url) and title.startswith(pattern):
            before_title = title
            title = title[len(pattern):].strip(title_strip)
    for urlpart, pattern in endswith:
        if (urlpart in url) and title.endswith(pattern):
            before_title = title
            title = title[:-len(pattern)].strip(title_strip)

    return title

class Web:
    """
    Opens a web page and returns urllib2 file object with results.

    It handles cookies, and sends IE8 user agent.
    """
    def __init__(self, spoof=True, agent=None):

        #Add cookie handling
##        self.cj = cookielib.LWPCookieJar()
##        if os.path.isfile('cookies.lwp'):
##            self.cj.load('cookies.lwp')
##        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cj))
##        urllib2.install_opener(opener)

        self.spoof = spoof
        if agent is None:
            #self.agent = 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0)'
            #self.agent = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.79 Safari/535.11'
            self.agent = "Mozilla/5.0 (Windows NT 6.1; WOW64) LK Test 1.0" 
        else:
            self.agent = agent

    def get(self, url, headers=None, **kwargs):
        """Gets web page, returns file object."""

        if headers is None:
            headers = {}

        for url_part, wait in ratelimit:
            if url_part not in url:
                continue

            lvlock.acquire()
            last = lastvisit.get(url_part, 0.0)
            lvlock.release()
            diff = time.time() - last

            while diff < wait:
                #print 'Rate limit \"%s\" caught: sleeping %f seconds.' % (url_part, wait-diff)
                time.sleep(wait-diff+0.01)

                lvlock.acquire()
                last = lastvisit.get(url_part, 0.0)
                lvlock.release()
                diff = time.time() - last

            lvlock.acquire()
            lastvisit[url_part] = time.time()
            lvlock.release()
        
        if 'forced_tuple' in kwargs:
            data = urllib.urlencode(kwargs['forced_tuple'])
        else:
            data = urllib.urlencode(kwargs)
        if data == '':
            data = None

        req = urllib2.Request(url, data, headers)
        
        if self.spoof:
            req.add_header('User-Agent', self.agent)

        f = urllib2.urlopen(req)

        return f

    def close(self, req):
        try:
            url = req.geturl()
        except:
            print 'Web close geturl error'
            return

        for url_part, wait in ratelimit:
            if url_part not in url:
                continue

            lvlock.acquire()
            lastvisit[url_part] = time.time()
            lvlock.release()

        try:
            req.close()
        except:
            print 'Web close error'
            return

    def title(self, url):
        try:
            if isinstance(url, (str, unicode)):
                r = self.get(url)
            else:
                r = url
                url = r.geturl()
            data = r.read()
            ct = r.headers.getparam('charset')
            r.close()
            try:
                data = data.decode(ct)
            except:
                data = data.decode('utf-8')
        except:
            return ''
        
        titles = re.findall('<title>([\w\W]*?)</title>', data, flags=re.UNICODE)
        if len(titles) == 0:
            return ''
        else:
            return title_parse(titles[0], url)
    

if __name__ == '__main__':
    s = time.time()
    t = ''
    for x in range(1000):
        t = title_parse("This is an example title | News", "http://en.wikipedia.org/wiki/hi")

    print time.time() - s
    print "'%s'" % t
