import cPickle as pickle
import os, os.path
import codecs

def linelist_load(fname):
    with codecs.open(fname, 'r', encoding='utf-8') as f:
        lines = map(unicode.strip, f.read().split('\n'))
        
    return lines
    
def linelist_save(fname, lines):
    with codecs.open(fname, 'w', encoding='utf-8') as f:
        r = list(set(lines))
        r.sort()
        f.write(u'\n'.join(r))

def pickle_load(s, default=None):
    try:
        f = open('store/%s.pk' % s, 'rb')
        ret = pickle.load(f)
        f.close()
    except:
        ret = default

    return ret

def pickle_save(name, obj):
    if not os.path.exists('store'):
        os.mkdir('store')
        
    f = open('store/%s.pk' % name, 'wb')
    pickle.dump(obj, f)
    f.close()

def repl_clean(s):
    return map(unicode.strip, s.rsplit('=', 1))
def repl_combine(repl_entry):
    return '='.join(repl_entry[:2]).lower()
def repl_ccombine(repl_entry):
    return '='.join(repl_entry[:2])

def repl_load(fname):
    with codecs.open(fname, 'r', encoding='utf-8') as f:
        rstring = f.read()

    return map(repl_clean, rstring.split('\n'))

def repl_save(repl, fname, preserve_case=False):
    if preserve_case:
        r = list(set(map(repl_ccombine, repl)))
    else:
        r = list(set(map(repl_combine, repl)))
    r.sort()
    rstring = '\n'.join(r)

    with codecs.open(fname, 'w', encoding='utf-8') as f:
        f.write(rstring)