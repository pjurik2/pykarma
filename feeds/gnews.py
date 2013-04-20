import rss

def gnews_link_filter(link):
    try:
        return link.rsplit('&url=', 1)[-1]
    except:
        return link

def gnews_watch():
    streams = ['http://news.google.com/news?pz=1&cf=all&ned=us&hl=en&topic=tc&output=rss',
               'http://news.google.com/news?pz=1&cf=all&ned=us&hl=en&topic=snc&output=rss',
               'http://news.google.com/news?pz=1&cf=all&ned=us&hl=en&topic=w&output=rss']

    rss.rss_watch(streams, 'Google', rss_link_filter=gnews_link_filter)

if __name__ == '__main__':
    gnews_watch()
