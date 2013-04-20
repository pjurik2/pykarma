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
