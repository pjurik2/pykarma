import web
import re

#w = web.Web()

import htmlentitydefs

def unescape(text):
    def fixup(m):
        text = m.group(0)
        if text[:2] == u"&#":
            # character reference
            try:
                if text[:3] == u"&#x":
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            # named entity
            try:
                text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text # leave as is
    try:
        return re.sub(u"&#?\w+;", fixup, text, re.UNICODE)
    except UnicodeDecodeError:
        return text


def jsonify(xml, level=0):
    ret = {}
    tags = all_tags_get(xml)
    if len(tags) == 0:
        return unescape(xml)
    
    for tag, attr, body in tags:
        #print ' ' * level, tag
        value = jsonify(body, level+1)

        if isinstance(value, (str, unicode)):
            if attr != '':
                d = attr_dict(attr)
                value = d
        else:
            if attr != '':
                value.update(attr_dict(attr))


        if tag in ret:
            if isinstance(ret[tag], list):
                ret[tag].append(value)
            else:
                ret[tag] = [ret[tag], value]
        else:
            ret[tag] = value

    return ret

def attr_dict(s):
    d = {}
    re.sub('\s+', ' ', s)
    attrs = s.split(' ')
    for attr in attrs:
        v = attr.split('=', 1)
        if len(v) == 1:
            continue
        key = v[0]
        value = v[1].strip('"\'')

        d[key] = value

    return d

def all_tags_get(xml):
    return re.findall('<(?P<tag>.*?)(?: (.*?))?>([\s\S]*?)</(?P=tag)>', xml)


if __name__ == '__main__':
    import web
    w = web.Web()
    url = 'http://feeds.bbci.co.uk/news/technology/rss.xml'
    r = w.get(url)
    d = r.read()

##    for item in jsonify(d)['rss']['channel']['item']:
##        print item['title']
##        print item['link'].rsplit('&url=', 1)[-1]

