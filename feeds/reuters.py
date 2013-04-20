import re
from rss import rss_watch

def reuters_linkr_filter(link):
    try:
        page = re.findall('(.*)\?feedType=', link)
        return page[0]
    except IndexError:
        return link

def reuters_watch():
    streams = ['http://feeds.reuters.com/reuters/technologyNews?format=xml',
               'http://feeds.reuters.com/reuters/worldNews?format=xml']

    rss_watch(streams, 'Reuters', rss_linkr_filter=reuters_linkr_filter,
              rmin=170, rmax=190)
        
if __name__ == '__main__':
    reuters_watch()
