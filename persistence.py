import cPickle as pickle

def pickle_load(s, default=None):
    try:
        f = open('%s.pk' % s, 'rb')
        ret = pickle.load(f)
        f.close()
    except:
        ret = default

    return ret

def pickle_save(name, obj):
    f = open('%s.pk' % name, 'wb')
    pickle.dump(obj, f)
    f.close()
