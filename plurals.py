import web
import json

w = web.Web()
word = 'butt'
url = """http://www.google.com/dictionary/json?callback=dict_api.callbacks.id100&q=%s&sl=en&tl=en&restrict=pr%%2Cde&client=te""" % word

print url
r = w.get(url)
d = r.read()
d = d[d.find('(')+1:d.rfind('}')+1]
print d[:5]
print d[-5:]
j = json.loads(d)

#print j
