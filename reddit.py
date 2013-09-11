import urllib
import urllib2
import json
import time
import web

url_filter = []
title_filter = []
agent = 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0)'

def get_submit_url(url, title, subreddit=''):
    req = urllib.urlencode({u'url': url.encode('utf-8'),
                            u'title': title.encode('utf-8')})

    if subreddit != '':
        submit_url = u'http://www.reddit.com/r/%s/submit?%s' % (subreddit,
                                                                req)
    else:
        submit_url = u'http://www.reddit.com/submit?%s' % req

    return submit_url

def reload_filters():
    global url_filter, title_filter

    with file('filters/filterurls.txt', 'r') as f:
        url_filter = map(str.strip, f.readlines())
    with file('filters/filtertitles.txt', 'r') as f:
        title_filter = map(str.strip, f.readlines())

reload_filters()

def get_karma(user='testname33'):
    w = web.Web()

    url = 'http://www.reddit.com/user/{user}/about.json'.format(user=user)
    
    while True:
        try:
            r = w.get(url)
            d = r.read()
            w.close(r)
        except:
            print 'link karma read error'
            time.sleep(31)
            continue

        try:
            user = json.loads(d)['data']
        except:
            print u'link karma json parse error: ', d
            time.sleep(5)
            continue

        return user.get('link_karma', 0)
    
def reddit_check_url(url, title=''):
    for s in title_filter:
        if s.lower() in title.lower():
            return 'filtered'

    for s in url_filter:
        if s.lower() in url.lower():
            return 'filtered'

    w = web.Web()

    query_string = urllib.urlencode({'url': url.encode('utf-8')})
    url = 'http://www.reddit.com/api/info.json?%s' % query_string
    
    data = ''
    while data == '':
        try:
            r = w.get(url)
            data = r.read()
            ct = r.headers.getparam('charset')
            w.close(r)
            try:
                data = data.decode(ct)
            except:
                try:
                    data = data.decode('utf-8')
                except:
                    print 'can\'t decode'
        except urllib2.HTTPError:
            print 'reddit check url HTTP error'
            time.sleep(3)

        except urllib2.URLError:
            print 'reddit check url network error'
            time.sleep(3)
    
    ret = []
    try:
        datad = json.loads(data)['data']['children']
    except:
        print 'reddit check url parse error'
        return 'error'

    for subd in datad:
        subd = subd['data']

        ret.append((subd.get('score', '0'),
                    subd.get('permalink', '')))

    return ret

if __name__ == '__main__':
    url = 'http://facebook.com'
    print reddit_check_url(url)
