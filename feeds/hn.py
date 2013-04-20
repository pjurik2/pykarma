import re
import random
import time
import json

import web

import urllib2

import reddit
from guiclient import new_rpc
import enc

USE_API = 2

def tag_get(tag, html):
    return re.findall('<%s(?: (.*?))?>(.*?)</%s>' % (tag, tag), html)

def all_tags_get(html):
    return re.findall('<(?P<tag>.*?)(?: (.*?))?>(.*?)</(?P=tag)>', html)

def attr_dict(s):
    """

    """
    d = {}
    re.sub('\s+', ' ', s)
    attrs = s.split(' ')
    for attr in attrs:
        v = attr.split('=', 1)
        if len(v) == 1:
            continue
        key = v[0]
        value = v[1].strip('"\'')

        d[key] = value

    return d
    
def hn_posts(url):
    html = ''
    while html == '':
        try:
            r = urllib2.urlopen(url)
            data = r.read()
            ct = r.headers.getparam('charset')
            r.close()
            try:
                data = data.decode(ct)
            except:
                data = data.decode('utf-8')
        except:
            print 'hn error'
            time.sleep(15)
            pass
        
    post = {}
    posts = []
    cells = tag_get('td', html)
    for attr, body in cells:
        tags = all_tags_get(body)
        
        attrd = attr_dict(attr)
        if attrd.get('class') == 'title':
            post = {}
            for t, a, b in tags:
                ad = attr_dict(a)
                if t == 'a':
                    #print b, '-', ad.get('href')
                    post['title'] = b
                    post['url'] = ad.get('href')

            if len(post) > 0:
                posts.append(post)
        elif attrd.get('class') == 'subtext':
            score = 0
            author = ''
            comments = 0
            for t, a, b in tags:
                ad = attr_dict(a)
                if t == 'span' and ad.get('id', '').startswith('score_'):
                    try:
                        score = int(b.split(' ')[0])
                    except:
                        score = 0
                elif t == 'a' and ad.get('href', '').startswith('user?id'):
                    author = b
                elif t == 'a' and ad.get('href', '').startswith('item?id'):
                    try:
                        comments = int(b.split(' ')[0])
                    except:
                        comments = 0
                        
            post['points'] = score
            post['author'] = author
            post['comments'] = comments
        else:
            pass

    return posts

def hn_watch():
    rpc = new_rpc('HN')
    w = web.Web()

    random.seed()
    tick = 0
    next_url = None
    urls = {}
    fail_count = 0
    datad = {}
    while True:
        if fail_count == 0:
            tick += 1
        else:
            next_url = None
        if tick == 4 or next_url is None:
            tick = 1
            if not USE_API:
                next_url = 'https://news.ycombinator.com/newest'
            elif USE_API == 2:
                next_url = 'http://hndroidapi.appspot.com/newest'
            else:
                next_url = 'http://api.ihackernews.com/new'

        print next_url
        if not USE_API:
            posts = hn_posts(next_url)
        elif USE_API == 2:
            try:
                r = urllib2.urlopen(next_url)
                data = r.read()
                ct = r.headers.getparam('charset')
                data = enc.decode(data, ct)
                        
            except:
                print 'network error'
                time.sleep(min(2 ** fail_count, 600))
                fail_count += 1
                continue

            try:
                datad = json.loads(data)
            except:
                print 'parse error'
                time.sleep(min(2 ** fail_count, 600))
                fail_count += 1
                continue
            posts = datad.get('items', [])   
        else:
            try:
                r = urllib2.urlopen(next_url)
                data = r.read()
                ct = r.headers.getparam('charset')
                try:
                    data = data.decode(ct)
                except:
                    data = data.decode('utf-8')
            except:
                print 'network error'
                time.sleep(min(2 ** fail_count, 600))
                fail_count += 1
                continue

            try:
                datad = json.loads(data)
            except:
                print 'parse error'
                time.sleep(min(2 ** fail_count, 600))
                fail_count += 1
                continue
            posts = datad.get('items', [])

        
        if len(posts) == 0:
            next_url = None
            time.sleep(min(2 ** fail_count, 600))
            fail_count += 1
            continue

        fail_count = 0

        if not USE_API:
            if posts[-1].get('title', '') == 'More':
                next_url = 'https://news.ycombinator.com' + posts[-1].get('url')
        elif USE_API == 2:
            next_url = None
        else:
            next_url = u'http://api.ihackernews.com/new/%s' % datad.get('nextId', '')
            
        points = [(int(post.get('points', 0)), i) for i, post in enumerate(posts)]
        points.sort()
        points = list(reversed(points))
        for post_id in points:
            post = posts[post_id[1]]

            if USE_API == 2:
                score = post.get('score', 0)
                try:
                    points = int(score.split(' ', 1)[0])
                except:
                    points = 0
                post['points'] = points
            
            if post.get('points', 0) < 3*tick:
                continue
            if post.get('url', '') in urls:
                continue
            else:
                urls[post['url']] = None

            if post['url'].startswith('http://'):
                title = w.title(post['url'])
                subreddit = rpc.subreddit(title)
                keywords = rpc.keywords(title)
                url = post['url']
                if reddit.url_output(title, subreddit, url, rpc):
                    rpc.linkadd('HN', title, url, subreddit, keywords)

        sleep_sec = random.randint(50, 70)
        sleep_step = sleep_sec / 10.0
        for x in range(10):
            time.sleep(sleep_step)
        
if __name__ == '__main__':
    hn_watch()
