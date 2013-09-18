# -*- coding: cp1252 -*-

import time
import threading
import re
import urllib2, urllib

from storage import *
from sanitize import *

rate_limits = [('reddit.com', 3.5)]

class Web:
    """
    Opens a web page and returns urllib2 file object with results.

    """
    def __init__(self, set_user_agent=True, agent=None):
        self.set_user_agent = set_user_agent
        if agent is None:
            self.agent = "PK Test 1.0" 
        else:
            self.agent = agent
            
        self.last_visits = {}
        self.last_visit_lock = threading.Lock()

    def get(self, url, headers=None, **kwargs):
        """Gets web page, returns file object."""

        if headers is None:
            headers = {}

        for url_part, wait in rate_limits:
            if url_part not in url:
                continue

            self.last_visit_lock.acquire()
            last = self.last_visits.get(url_part, 0.0)
            self.last_visit_lock.release()
            diff = time.time() - last

            while diff < wait:
                #print 'Rate limit \"%s\" caught: sleeping %f seconds.' % (url_part, wait-diff)
                time.sleep(wait-diff+0.01)

                self.last_visit_lock.acquire()
                last = self.last_visits.get(url_part, 0.0)
                self.last_visit_lock.release()
                diff = time.time() - last

            self.last_visit_lock.acquire()
            self.last_visits[url_part] = time.time()
            self.last_visit_lock.release()
        
        if 'forced_tuple' in kwargs:
            data = urllib.urlencode(kwargs['forced_tuple'])
        else:
            data = urllib.urlencode(kwargs)
        if data == '':
            data = None

        req = urllib2.Request(url, data, headers)
        
        if self.set_user_agent:
            req.add_header('User-Agent', self.agent)

        f = urllib2.urlopen(req)

        return f

    def close(self, req):
        try:
            url = req.geturl()
        except:
            print 'Web close geturl error'
            return

        for url_part, wait in rate_limits:
            if url_part not in url:
                continue

            self.last_visit_lock.acquire()
            self.last_visits[url_part] = time.time()
            self.last_visit_lock.release()

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
    

