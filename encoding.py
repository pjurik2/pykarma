import re
import htmlentitydefs

allc = map(chr, range(256))
ok = '\t\n\r' + ''.join(map(chr, range(32, 127)))
nok = ''.join(set(allc) - set(ok))

def decode(data, ct):
    try:
        return data.decode(ct)
    except:
        try:
            return data.decode('utf-8')
        except:
            return unicode(last_resort(data))

def last_resort(string):
    return string.translate(None, nok)

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


def all_tags_get(xml):
    return re.findall('<(?P<tag>.*?)(?: (.*?))?>([\s\S]*?)</(?P=tag)>', xml)
