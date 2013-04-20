from rss import RSSFeed

class PhysorgFeed(RSSFeed):
    def configure(self):
        self.title = 'Physorg'
        self.wait_range = (300, 330)
        self.streams = ['http://www.physorg.com/rss-feed/']
        
if __name__ == '__main__':
    f = PhysorgFeed()
    f.watch()
