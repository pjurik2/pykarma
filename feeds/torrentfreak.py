from rss import RSSFeed


class TorrentfreakFeed(RSSFeed):
    def configure(self):
        self.streams = ['http://feed.torrentfreak.com/Torrentfreak/']
        self.title = 'TorrentFreak'
        self.max_subs = 1

    def url_post_filter(self, url):
        return url.split('/?utm_source=')[0]

if __name__ == '__main__':
    f = TorrentfreakFeed()
    f.watch()
