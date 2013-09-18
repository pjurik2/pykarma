import json
import time
import re
import threading
import copy

import web
from storage import *
from sanitize import get_keywords

SUBREDDIT_NEW_POSTS_URL = 'http://www.reddit.com/r/%s/new/.json?sort=new&t=all&count=%d&after=%s'

class TitleStats:
    def __init__(self):
        self.lock = threading.Lock()
        
        self.removed_keywords = linelist_load('filters/removed_keywords.txt')
        self.words = pickle_load('words', {})
        self.subs = pickle_load('subs', {})
        self.titles = pickle_load('titles', [])
        self.link_names = pickle_load('links', {})
        
        self.keyword_counts_recent = {}
        self.keyword_titles_recent = {}
        self.keyword_counts_newest = {}
        self.keyword_titles_newest = {}
        self.correct = 0
        
        self.removed_subreddits = linelist_load('filters/removed_subreddits.txt')
        self.allowed_subreddits = linelist_load('filters/allowed_subreddits.txt')
        self.subreddit_queue = copy.copy(self.allowed_subreddits)

        self.active_subreddit = self.subreddit_queue.pop()

    def word_count(self, word, quiet=True):
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

        count = self.words[word][u'all']
        self.lock.release()
        return count

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
        
    def stats(self, title, keywords=None):
        # TODO: Make this more efficient by using intermediate values from
        #       other functions of this class
        
        if keywords is None:
            keywords = self.keywords(title)
            
        kws = keywords.split(' ')
        total_count = 0
        unk_word = 0
        for kw in kws:
            if kw.startswith('-'):
                kw = kw[1:]
                
            wc = self.word_count(kw, quiet=False)

            if wc == 0:
                unk_word += 1
            else:
                total_count += wc

        total_inv = 0
        matched_inv = 0
        if total_count != 0:
            total_count = float(total_count)
            for kw in kws:
                if kw[0] == '-':
                    kww = kw[1:]
                else:
                    kww = kw
                    
                try:
                    inv_ratio = total_count / self.word_count(kww)
                except ZeroDivisionError:
                    continue
                    
                if kw[0] == '-':
                    matched_inv += inv_ratio
                    
                total_inv += inv_ratio
                

        if len(kws) == 0:
            staleness_ratio = 1.0
        else:
            try:
                staleness_ratio = matched_inv / total_inv
            except ZeroDivisionError:
                staleness_ratio = 0.0

        sub_pairs = self.identify_list(title)
        if len(sub_pairs) > 1:
            try:
                relative_certainty = sub_pairs[0][0] / sub_pairs[1][0]
            except:
                print 'sub_ratio calculation error'
                relative_certainty = 1.0
        else:
            if len(sub_pairs) == 0:
                sub_pairs = ((0.0, 'none'),)
            relative_certainty = 1.0
            
        match_strength = sub_pairs[0][0]
        
        return match_strength, relative_certainty, staleness_ratio

    def keywords(self, title):
        self.lock.acquire()
        ret = self.keywords_work(title, s=False)
        if len(ret) == 0:
            self.lock.release()
            return ''
        
        new_ret = []
        matched = [(0.0, '')]

        for w in ret:
            if w in self.keyword_counts_recent:
                matched.append(self.most_matched(title, self.keyword_titles_recent[w]))
            elif w in self.keyword_counts_newest:
                matched.append(self.most_matched(title, self.keyword_titles_newest[w]))
                                            
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
        title_keywords = get_keywords(title)
        keywords = []
        for w in title_keywords:
            if w in self.removed_keywords:
                continue
            keywords.append(w)

        if s:
            return ' '.join(keywords)
        else:
            return keywords

    def identify(self, title):
        self.lock.acquire()
        while self.keyword_counts_recent == {}:
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
        title_keywords = self.keywords_work(title, s=False)
        sub_counts = {}
        for w in title_keywords:
            if w in self.words:
                if self.words[w] is None:
                    continue

                for k, v in self.words[w].iteritems():
                    # don't use excluded subreddits
                    if k.lower() in self.removed_subreddits:
                        continue
                        
                    # don't return subreddits with less than 10000 keywords of training
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
        title_keywords = get_keywords(title)

        if page == 0:
            for w in title_keywords:
                self.keyword_counts_newest[w] = self.keyword_counts_newest.get(w, 0)+1
                self.keyword_titles_newest[w] = self.keyword_titles_newest.get(w, [])+[title]

        if name in self.link_names:
            self.lock.release()
            return False

        self.titles.append(title)
        self.link_names[name] = None

        guess = self.identify_work(title)
        if guess == sub:
            self.correct += 1

        self.subs[sub] = self.subs.get(sub, 0) + len(title_keywords)

        for w in title_keywords:
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
        after = None #results token
        
        i = 0
        first_round = True
        w = web.Web()
        while crawl == 0 or i < crawl:
            if after is None:
                url = 'http://www.reddit.com/r/%s/new/.json?sort=new&t=all' % self.active_subreddit
            else:
                url = SUBREDDIT_NEW_POSTS_URL % (self.active_subreddit, i*25, after)
                
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
                if len(self.subreddit_queue) == 0:
                    self.subreddit_queue = copy.copy(self.allowed_subreddits)
                    first_round = False

                    self.lock.acquire()
                    self.keyword_counts_recent = copy.copy(self.keyword_counts_newest)
                    self.keyword_titles_recent = copy.copy(self.keyword_titles_newest)
                    self.keyword_counts_newest = {}
                    self.keyword_titles_newest = {}
                    self.lock.release()
                    
                i = 0

                pre_active_subreddit = self.active_subreddit
                self.active_subreddit = self.subreddit_queue.pop()
                after = None
                
                if not first_round:
                    time.sleep(10)
                    continue
                else:
                    print 'Crawled /r/%s -' % pre_active_subreddit, \
                    '%d/%d links were new. Training: %d sorted correctly.' % (new, len(links), self.correct), \
                    'Now storing:', len(self.words), 'words,', len(self.subs), \
                    'subs,', len(self.link_names), 'links'
                    time.sleep(3)
                    continue


            retest_correct = self.test(links)
            print 'Crawled /r/%s -' % self.active_subreddit, \
                  '%d/%d links were new. Training: %d -> %d sorted correctly.' % \
                  (new, len(links), self.correct, retest_correct), \
                  'Now storing:', len(self.words), 'words,', len(self.subs), \
                  'subs,', len(self.link_names), 'links'

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


    
