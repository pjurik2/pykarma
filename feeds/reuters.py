import re
from rss import RSSFeed

class ReutersFeed(RSSFeed):
    def configure(self):
        self.streams = ['http://feeds.reuters.com/reuters/technologyNews?format=xml',
                        'http://feeds.reuters.com/reuters/worldNews?format=xml']
        self.title = 'Reuters'

        self.wait_range = (170, 190)

        
    def url_post_filter(self, link):
        try:
            page = re.findall('(.*)\?feedType=', link)
            return page[0]
        except IndexError:
            return link

if __name__ == '__main__':
    f = ReutersFeed()
    f.watch()
