import re
from rss import RSSFeed

class ArsTechnicaFeed(RSSFeed):
    def configure(self):
        self.streams = ['http://feeds.arstechnica.com/arstechnica/index?format=xml']
        self.title = 'Ars'
        self.wait_range = (120, 130)

    def url_post_filter(self, url):
        try:
            page = re.findall('arstechnica\\.com/(.*?\\.ars)', url)
            return 'http://arstechnica.com/%s' % page[0]
        except IndexError:
            return url
        
if __name__ == '__main__':
    f = ArsTechnicaFeed()
    f.watch()
