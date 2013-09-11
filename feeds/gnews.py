import rss
from rss import RSSFeed

class GoogleNewsFeed(RSSFeed):
    def configure(self):
        self.title = 'Google'
        self.streams = ['http://news.google.com/news?pz=1&cf=all&ned=us&hl=en&topic=tc&output=rss',
                        'http://news.google.com/news?pz=1&cf=all&ned=us&hl=en&topic=snc&output=rss',
                        'http://news.google.com/news?pz=1&cf=all&ned=us&hl=en&topic=w&output=rss']


    def url_pre_filter(self, link):
        try:
            return link.rsplit('&url=', 1)[-1]
        except:
            return link

if __name__ == '__main__':
    f = GoogleNewsFeed()
    f.watch()
