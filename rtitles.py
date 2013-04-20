# -*- coding: cp1252 -*-
##import socks
##import socket
##socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, "127.0.0.1", 8080)
##socket.socket = socks.socksocket

import json
import time
import re
import threading
from copy import copy
import codecs
import web

from persistence import pickle_load, pickle_save
from repl import *

def re_ccompiler(terms):
    return re_compiler(terms, re.IGNORECASE)

def re_compiler(terms, cflags=0):
    cflags |= re.UNICODE
    c = re.compile(u"(\W|\A)%s(\W|\Z)" % re.escape(terms[0]),
                   flags=cflags)
    return c, r"\1(%s)\2" % terms[1]

replace_words = dict(repl_load('wordreplace.txt'))

replace = repl_load('kreplace.txt')
replace_dict = dict(replace)
r_str = '|'.join(map(re.escape, list(replace_dict.iterkeys())))
replace_filter = re.compile(u"(\W|\A)(%s)(\W|\Z)" % r_str, flags=(re.UNICODE|re.IGNORECASE))


replace_cased = repl_load('kcreplace.txt')
replace_cased_dict = dict(replace_cased)
rc_str = '|'.join(map(re.escape, list(replace_cased_dict.iterkeys())))
replace_cased_filter = re.compile(u"(\W|\A)(%s)(\W|\Z)" % rc_str, flags=re.UNICODE)

def replc(m):
    global replace_cased_dict
    g2 = replace_cased_dict.get(m.group(2), m.group(2))
    return m.group(1) + g2 + m.group(3)

def repl(m):
    global replace_dict
    g2 = replace_dict.get(m.group(2).lower(), m.group(2))
    return m.group(1) + g2 + m.group(3)


filter_num_commas = re.compile(u'([0-9]+),(?=[0-9]+)', flags=re.UNICODE)
filter_apostrophes = re.compile(u'(\W*)((?:\w\S*?\w)|(?:\w+?))(?:\'|’|’|‘)s(\W*)',
                                flags=re.UNICODE)

find_words = re.compile(u'\W*((?:\w\S*\w)|(?:\w+))\W*',
                        flags=re.UNICODE)

def get_words(s):
    global replace
    global filter_num_commas, filter_apostrophes, find_words

    global replace_filter, replace_cased_filter

    s = s.replace('--', ' ')
    s = filter_num_commas.sub(r'\1', s)
    s = filter_apostrophes.sub(r'\1\2\3', s)

    s = replace_filter.sub(repl, s)
    s = replace_cased_filter.sub(replc, s)

    l = find_words.findall(s.lower())

    for i in range(len(l)):
        if l[i] in replace_words:
            l[i] = replace_words[l[i]]

    l = list(set(l))
    l.sort()
    
    return l

sub_ignore = ['blog', 'askreddit', 'self', 'pics', 'videos', 'gifs', 'all']
word_ignore = []


ncrawl_queue = ['technology', 'programming', 'worldnews', 'science',
                'politics', 'atheism', 'Music', 'movies',
                'trees', 'soccer', 'nfl', 'canada', 'news', 'nba',
                'Android', 'books', 'hockey', 'food', 'Drugs',
                'netsec', 'Space', 'geek', 'Health', 'Environment',
                'Business', 'economy', 'Apple', 'Android', 'Google', 'Microsoft']

crawl_queue = copy(ncrawl_queue)

crawl_sub = crawl_queue.pop()
new_url_format = 'http://www.reddit.com/r/%s/new/.json?sort=new&t=all&count=%d&after=%s'

class TitleStats:
    def __init__(self):
        self.lock = threading.Lock()
        self.since_save = 0
        with codecs.open('common.txt', 'r', encoding='utf-8') as f:
            self.common = map(unicode.strip, f.read().split('\n'))
            
        self.words = pickle_load('words', {})
        self.subs = pickle_load('subs', {})
        self.titles = pickle_load('titles', [])
        self.link_names = pickle_load('links', {})
        
        self.subs_recent = {}
        self.subs_trecent = {}
        self.subs_newest = {}
        self.subs_tnewest = {}
        self.correct = 0

    def word_count(self, word, quiet=False):
        self.lock.acquire()

        if word not in self.words:
            if not quiet:
                print 'Interesting word:', word
            self.lock.release()
            return 0

        if u'all' not in self.words[word]:
            if not quiet:
                print 'Rare interesting word:', word
            self.lock.release()
            return 0

        self.lock.release()
        return self.words[word][u'all']

    def most_matched(self, test_title, recent_titles):
        test_keywords = self.keywords_work(test_title)
        if len(test_keywords) == 0:
            return 0.0, ''

        matched = [(0.0, '')]
        for t in recent_titles:
            recent_keywords = self.keywords_work(t)

            common_keywords = len(set(test_keywords) & set(recent_keywords))

            ratio = float(common_keywords) / len(test_keywords)

            matched.append((ratio, t))

        matched.sort()

        return matched[-1]
        

    def keywords(self, title):
        self.lock.acquire()
        ret = self.keywords_work(title, s=False)
        if len(ret) == 0:
            self.lock.release()
            return ''
        
        new_ret = []
        matched = [(0.0, '')]

        for w in ret:
            if w in self.subs_recent:
                matched.append(self.most_matched(title, self.subs_trecent[w]))
            elif w in self.subs_newest:
                matched.append(self.most_matched(title, self.subs_tnewest[w]))
                                            
        matched.sort()

        matched_keywords = self.keywords_work(matched[-1][1])
        for w in ret:
            if w in matched_keywords:
                new_ret.append('-%s' % w)
            else:
                new_ret.append(w)

        ret = ' '.join(new_ret)
        self.lock.release()
        return ret

    def keywords_work(self, title, s=True):
        title_words = get_words(title)
        keywords = []
        for w in title_words:
            if w in self.common:
                continue
            keywords.append(w)

        if s:
            return ' '.join(keywords)
        else:
            return keywords

    def identify(self, title):
        self.lock.acquire()
        while self.subs_recent == {}:
            self.lock.release()
            time.sleep(1)
            self.lock.acquire()
            
        ret = self.identify_work(title)
        self.lock.release()
        return ret
        
    def identify_work(self, title):
        sub_pairs = self.identify_list_work(title)
        if len(sub_pairs) > 0:
            return sub_pairs[0][1]
        else:
            return ''
        
    def identify_list(self, title):
        self.lock.acquire()
        ret = self.identify_list_work(title)
        self.lock.release()
        return ret

    def identify_list_work(self, title):
        title_words = self.keywords_work(title, s=False)
        sub_counts = {}
        for w in title_words:
            if w in word_ignore:
                continue
            
            if w in self.words:
                if self.words[w] is None:
                    continue

                for k, v in self.words[w].iteritems():
                    if k.lower() in sub_ignore:
                        continue
                    if self.subs[k] < 10000:
                        continue

                    sub_counts[k] = sub_counts.get(k, 0.0) + ((float(v) / self.subs[k]) / (self.words[w][u'all']**0.4))

        sub_pairs = zip(list(sub_counts.itervalues()), list(sub_counts.iterkeys()))
        sub_pairs.sort()
        sub_pairs = list(reversed(sub_pairs))

        return sub_pairs
                
    def add_link(self, link, page=1):
        self.lock.acquire()
        name = link.get('name', '')
        
        title = link.get('title', '')
        sub = link.get('subreddit', '')
        title_words = get_words(title)

        if page == 0:
            for w in title_words:
                self.subs_newest[w] = self.subs_newest.get(w, 0)+1
                self.subs_tnewest[w] = self.subs_tnewest.get(w, [])+[title]

        if name in self.link_names:
            self.lock.release()
            return False

        self.titles.append(title)
        self.link_names[name] = None

        guess = self.identify_work(title)
        if guess == sub:
            self.correct += 1

        self.subs[sub] = self.subs.get(sub, 0) + len(title_words)

        for w in title_words:
            if w in self.words:
                if self.words[w] is None:
                    continue
                
                self.words[w][sub] = self.words[w].get(sub, 0)+1
                self.words[w][u'all'] = self.words[w].get(u'all', 0)+1
            else:
                self.words[w] = {sub: 1, u'all': 1}

        self.lock.release()
        return True
                
    def crawl(self, crawl=0):
        global crawl_sub, crawl_queue, ncrawl_queue

        after = None #results token
        
        i = 0
        first_round = True
        w = web.Web()
        while crawl == 0 or i < crawl:
            if after is None:
                url = 'http://www.reddit.com/r/%s/new/.json?sort=new&t=all' % crawl_sub
            else:
                url = new_url_format % (crawl_sub, i*25, after)
                
            if first_round:
                print 'Crawling', url
                
            try:
                r = w.get(url)
                d = r.read()
                w.close(r)
            except:
                r = None
                print 'reddit crawler network error'
                time.sleep(5)
                continue

            try:
                data = json.loads(d)['data']
                links = data['children']
                after = data.get('after', None)
            except:
                print 'reddit crawler parse error'
                time.sleep(5)
                continue

            self.correct = 0
            new = len(links)
            for link in links:
                link = link.get('data', {})
                if not self.add_link(link, i):
                    new -= 1

            if new == 0 or first_round:
                if len(crawl_queue) == 0:
                    crawl_queue = copy(ncrawl_queue)
                    first_round = False

                    self.lock.acquire()
                    self.subs_recent = copy(self.subs_newest)
                    self.subs_trecent = copy(self.subs_tnewest)
                    self.subs_newest = {}
                    self.subs_tnewest = {}
                    self.lock.release()
                    
                i = 0

                pre_crawl_sub = crawl_sub
                crawl_sub = crawl_queue.pop()
                after = None
                
                if not first_round:
                    time.sleep(10)
                    continue
                else:
                    print 'Crawled /r/%s -' % pre_crawl_sub, len(self.words), 'words,', len(self.subs), 'subs,', '%d/%d links (%d/%d new)' % (len(links), len(self.link_names), self.correct, new)
                    time.sleep(3)
                    continue


            retest_correct = self.test(links)
            print 'Crawled /r/%s -' % crawl_sub, len(self.words), 'words,', len(self.subs), 'subs,', '%d/%d links (%d/%d/%d new)' % (len(links), len(self.link_names), self.correct, retest_correct, new)

            time.sleep(3)
            i += 1
            self.save()

    def test(self, links):
        correct = 0
        new = len(links)
        for link in links:
            link = link.get('data', {})
            title = link.get('title', '')
            sub = link.get('subreddit', '')
            if self.identify(title) == sub:
                correct += 1

        return correct
                
    def save(self):
        pickle_save('words', self.words)
        pickle_save('subs', self.subs)
        pickle_save('links', self.link_names)
        pickle_save('titles', self.titles)

if __name__ == '__main__':
    r = [None] * 100
    s = time.time()
    for x in range(100):
        r[x] = get_words("asdf this is AI ai really neat barack obama is nkorea")

    print time.time() - s
    print r[-1]
    
