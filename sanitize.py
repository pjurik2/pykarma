# -*- coding: cp1252 -*-

import threading
from copy import copy
import codecs
import web
import re, time
import encoding

from storage import *

replaced_keywords = dict(repl_load('filters/replaced_keywords.txt'))

replaced_phrases_dict = dict(repl_load('filters/replaced_phrases.txt'))
r_str = '|'.join(map(re.escape, list(replaced_phrases_dict.iterkeys())))
replaced_phrases_filter = re.compile(u"(\W|\A)(%s)(\W|\Z)" % r_str, flags=(re.UNICODE|re.IGNORECASE))


replaced_string_dict = dict(repl_load('filters/replaced_strings.txt'))
rc_str = '|'.join(map(re.escape, list(replaced_string_dict.iterkeys())))
replaced_string_filter = re.compile(u"(\W|\A)(%s)(\W|\Z)" % rc_str, flags=re.UNICODE)

filter_num_commas = re.compile(u'([0-9]+),(?=[0-9]+)', flags=re.UNICODE)
filter_apostrophes = re.compile(u'(\W*)((?:\w\S*?\w)|(?:\w+?))(?:\'|’|’|‘)s(\W*)',
                                flags=re.UNICODE)
find_words = re.compile(u'\W*((?:\w\S*\w)|(?:\w+))\W*',
                        flags=re.UNICODE)
                        
def replc(m):
    global replaced_string_dict
    g2 = replaced_string_dict.get(m.group(2), m.group(2))
    return m.group(1) + g2 + m.group(3)

def repl(m):
    global replaced_phrases_dict
    g2 = replaced_phrases_dict.get(m.group(2).lower(), m.group(2))
    return m.group(1) + g2 + m.group(3)
    
def get_keywords(s):
    global replace
    global filter_num_commas, filter_apostrophes, find_words

    global replaced_phrases_filter, replaced_string_filter

    # Replace double dashes with a space
    s = s.replace('--', ' ')
    
    # Remove commas from numbers
    s = filter_num_commas.sub(r'\1', s)
    
    # Remove apostrophes from phrases
    s = filter_apostrophes.sub(r'\1\2\3', s)

    # Replace phrases with other phrases (case-insensitive)
    s = replaced_phrases_filter.sub(repl, s)
    
    # Replace strings with other strings (case-sensitive)
    s = replaced_string_filter.sub(replc, s)

    # Split title into keywords
    l = find_words.findall(s.lower())

    # Replace keywords with other keywords
    for i in range(len(l)):
        if l[i] in replaced_keywords:
            l[i] = replaced_keywords[l[i]]

    # Return sorted, unique keywords
    l = list(set(l))
    l.sort()
    
    return l
    
removed_title_endings = repl_load('filters/removed_title_endings.txt')
removed_title_beginnings = repl_load('filters/removed_title_beginnings.txt')
title_strip = u'\r\n\t -:«»||•—'
    
def title_parse(title, url=''):
    global removed_title_beginnings, removed_title_endings, title_strip
    
    title = encoding.unescape(title).strip().strip(title_strip)
    title = re.sub(u'\s+', u' ', title, flags=re.UNICODE)

    for urlpart, pattern in removed_title_beginnings:
        if (urlpart in url) and title.startswith(pattern):
            title = title[len(pattern):].strip(title_strip)
            
    for urlpart, pattern in removed_title_endings:
        if (urlpart in url) and title.endswith(pattern):
            title = title[:-len(pattern)].strip(title_strip)

    return title
    
if __name__ == '__main__':
    print get_keywords("asdf this is AI ai really neat barack obama is nkorea")
    