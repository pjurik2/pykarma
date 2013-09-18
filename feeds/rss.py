import os, sys
import random
import time
import feedparser
import itertools
import HTMLParser


from feed import Feed
if os.getcwd().rstrip(os.sep).endswith('feeds'):
    os.chdir('..')
    sys.path.insert(0, os.getcwd())

from gui_client import new_rpc
import web
import reddit

class RSSFeed(Feed):
    def __init__(self):
        self.title = 'RSS Feed'
        self.streams = []
        self.wait_range = (60, 70)
        self.max_error_wait = 600
        self.max_subs = 0
        
        self.urls = set()

    def configure(self):
        pass

    def watch(self, new_streams=None):
        self.configure()
        self.web = web.Web()

        try:
            self.rpc = new_rpc(self.title)
        except:
            self.rpc = None
            print 'Warning: Running without RPC'
        
        if new_streams is None:
            new_streams = []
            
        streams = self.streams + new_streams

        for url in itertools.cycle(streams):
            print url
            self.check_feed(url)
            time.sleep(random.randint(*self.wait_range))

    def check_feed(self, url):
        for fail_count in itertools.count():
            try:
                datad = feedparser.parse(url)
            except:
                print 'Parse error for', url
                time.sleep(min(2 ** fail_count, self.max_error_wait))
            else:
                break

        try:
            posts = datad['items']
        except:
            print 'No items field for', url
            posts = []

        for post in posts:
            self.check_post(post)

    def check_post(self, post):
        if ('link' not in post):
            return False
        
        url = self.url_pre_filter(post['link'])

        try:
            req = self.web.get(url)
            url = req.geturl()
        except:
            print 'URL retrieval error for ', url
            return False

        url = self.url_post_filter(url)
            
        if (url in self.urls) or not url.startswith('http://'):
            return False
        
        self.urls.add(url)

        feed_title = self.default_title_filter(post.get('title', ''))
        page_title = self.default_title_filter(self.web.title(req))
        title = self.title_filter(page_title, feed_title)

        if self.rpc is not None:
            subreddit = self.rpc.get_title_subreddit(title)
            keywords = self.rpc.get_title_keywords(title)
            
            if self.rpc.get_link_posted_count(url, title) <= self.max_subs:
                stats = self.rpc.get_learned_stats(title, keywords)
                self.rpc.gui_link_add(self.title, title, url, subreddit, keywords, **stats)

        try:
            req.close()
        except:
            pass

        print title
        print url

    def url_pre_filter(self, url):
        return url

    def url_post_filter(self, url):
        return url

    def default_title_filter(self, title):
        h = HTMLParser.HTMLParser()
        return h.unescape(title)

    def title_filter(self, page_title, feed_title):
        return page_title
        
if __name__ == '__main__':
    f = RSSFeed()
    f.watch(['http://www.physorg.com/rss-feed/'])
