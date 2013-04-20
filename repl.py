import codecs

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
