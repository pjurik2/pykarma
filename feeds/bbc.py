from rss import RSSFeed

class BBCFeed(RSSFeed):
    def configure(self):
        self.streams = ['http://feeds.bbci.co.uk/news/world/rss.xml',
                        'http://feeds.bbci.co.uk/news/technology/rss.xml']
        self.title = 'BBC'

    def url_pre_filter(self, url):
        try:
            return url.rsplit('&url=', 1)[-1]
        except:
            return url
        
if __name__ == '__main__':
    f = BBCFeed()
    f.watch()
