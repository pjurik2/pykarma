import out

import wx
import threading
import webbrowser
import time

import pyperclip

import reddit_titles
from guiserv import GUIServer
from storage import *
import reddit

HOST = 'localhost'
PORT = 9367

class FileOutput:
    def __init__(self, root):
        self.root = root
        self.line_written = False
        
    def write(self, text):
        if text == '\n':
            self.out(text)
            self.line_written = False
        elif self.line_written:
            self.out(text)
        else:
            self.out("[%s] %s" % (time.strftime('%X'), text))
            self.line_written = True

    def out(self, *args, **kwargs):
        wx.CallAfter(self.root.out_append, *args, **kwargs)

class GUIMain:
    def __init__(self):
        reddit.reload_filters()
        self.check_cache = {}
        self.links_queued = pickle_load('linksqueued', {})
        self.links_checked = pickle_load('linkschecked', {})
        
        self.menu_idx = 0
        self.links_lock = threading.Lock()
        self.check_lock = threading.Lock()
        self.url_next = None
        self.title_stats = reddit_titles.TitleStats()
        self.rtitles_thread = threading.Thread(target=self.title_stats.crawl)
        self.rtitles_thread.start()
        
        self.server = GUIServer(self, HOST, PORT)
        self.server.serve()

        self.app = wx.App()
        self.frame = wx.Frame(None, -1, 'Karma Krawler')

        self.sizer = wx.GridBagSizer()
        self.sizer.AddGrowableCol(0, 10)
        self.sizer.AddGrowableRow(1, 10)
        self.sizer.AddGrowableRow(2, 15)
        

        self.karma = wx.StaticText(self.frame,
                                   style=wx.ALIGN_CENTRE)
        self.karma.SetLabel('Link Karma: Unknown')

        self.karma_font = wx.Font(24, wx.FONTFAMILY_DEFAULT,
                                  wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)

        self.karma.SetFont(self.karma_font)
        self.karma.SetBackgroundColour('white')
        self.karma.SetForegroundColour('red')
        
        self.sizer.Add(self.karma, pos=(0, 0), flag=wx.EXPAND)

        self.out = wx.TextCtrl(self.frame, size=(1200, 200),
                               style=(wx.TE_READONLY | wx.TE_MULTILINE | wx.TE_AUTO_URL | wx.TE_RICH2 | wx.TE_NOHIDESEL))
        self.out.Bind(wx.EVT_TEXT_URL, self.url_open)
        self.out.Bind(wx.EVT_LEFT_UP, self.url_open2)

        self.sizer.Add(self.out, pos=(1, 0), flag=wx.EXPAND)

        self.links = wx.ListCtrl(self.frame, size=(1200, 200),
                                style=wx.LC_REPORT)
        
        self.links.InsertColumn(0, 'Source', width=75)
        self.links.InsertColumn(1, 'Title', width=375)
        self.links.InsertColumn(2, 'URL', width=200)
        self.links.InsertColumn(3, 'Subreddit', width=97)
        self.links.InsertColumn(4, 'Keywords', width=375)

        self.links.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.links_activate)
        self.links.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.links_right)
        self.links.Bind(wx.EVT_LIST_KEY_DOWN, self.link_keypress)

        for url, link in self.links_queued.iteritems():
            self.links_append(*link, force=True)
        
        self.sizer.Add(self.links, pos=(2, 0), flag=wx.EXPAND)

        self.fout = FileOutput(self)
        out.set_output('Main', self.fout)

        self.frame.SetSizerAndFit(self.sizer)
        self.frame.Show()
        self.app.MainLoop()

    def set_karma(self, karma):
        self.karma.SetLabel('Link Karma: %s' % karma)
        self.sizer.Layout()

    def link_check(self, url, title=''):
        self.links_lock.acquire()
        if url in self.links_checked:
            self.links_lock.release()
            return 10

        if url not in self.check_cache:
            self.links_lock.release()
            self.check_lock.acquire()
            val = len(reddit.reddit_check_url(url, title))
            self.check_lock.release()
            self.links_lock.acquire()
            self.check_cache[url] = val

        self.links_lock.release()
        return self.check_cache[url]            

    def links_save(self):
        pickle_save('linksqueued', self.links_queued)
        pickle_save('linkschecked', self.links_checked)

    def links_append_safe(self, *args, **kwargs):
        wx.CallAfter(self.links_append, *args, **kwargs)

    def links_append(self, source, title, url, subreddit, keywords='',
                    force=False):
        self.links_lock.acquire()
        if url in self.links_checked or \
           ((url in self.links_queued) and not force) or\
           title == '':
            self.links_lock.release()
            return

        kws = keywords.split(' ')
        found = 0
        total_count = 0
        unk_word = 0
        for kw in kws:
            if kw.startswith('-'):
                found += 1
                try:
                    wc = self.title_stats.word_count(kw[1:])
                except ZeroDivisionError:
                    continue
            else:
                try:
                    wc = self.title_stats.word_count(kw)
                except ZeroDivisionError:
                    continue

            if wc == 0:
                unk_word += 1
            else:
                total_count += wc

        total_inv = 0
        matched_inv = 0
        if total_count != 0:
            total_count = float(total_count)
            for kw in kws:
                if kw.startswith('-'):
                    try:
                        inv_ratio = total_count / self.title_stats.word_count(kw[1:], quiet=True)
                    except ZeroDivisionError:
                        continue
                    matched_inv += inv_ratio
                else:
                    try:
                        inv_ratio = total_count / self.title_stats.word_count(kw, quiet=True)
                    except ZeroDivisionError:
                        continue
                total_inv += inv_ratio
                

        if len(kws) == 0:
            ratio = 1.0
        else:
            try:
                ratio = matched_inv / total_inv
            except ZeroDivisionError:
                ratio = 0.0

        if ratio == 1.0:
            self.links_lock.release()
            return

        sub_pairs = self.title_stats.identify_list(title)
        if len(sub_pairs) > 1:
            try:
                sub_ratio = sub_pairs[0][0] / sub_pairs[1][0]
            except:
                print 'sub_ratio calculation error'
                sub_ratio = 1.0
        else:
            if len(sub_pairs) == 0:
                sub_pairs = ((0.0, 'none'),)
            sub_ratio = 1.0

        if (len(kws)-unk_word) < 3 or ratio > 0.30 or subreddit == '':
            color = 0x990000

        else:
            color = 0x009900
            
        
        self.links_queued[url] = (source, title, url, subreddit, keywords)
        self.links_save()
        
        i = self.links.GetItemCount()
        self.links.InsertStringItem(i, '')
        self.links.SetStringItem(i, 0, source)
        self.links.SetStringItem(i, 1, title)
        self.links.SetStringItem(i, 2, url)
        self.links.SetStringItem(i, 3, "%s" % subreddit)
        self.links.SetStringItem(i, 4, "(%f/%f) (%f) %s" % (sub_pairs[0][0], sub_ratio, ratio, keywords))

        self.links.SetItemTextColour(i, wx.Colour((color&0xFF0000)>>16,
                                                  (color&0x00FF00)>>8,
                                                  (color&0x0000FF)))
        
        self.links.ScrollList(0, 1000)
        self.links_lock.release()

    def links_right(self, evt):
        self.links_lock.acquire()
        i = evt.GetIndex()
        self.menu_idx = i

        menu = wx.Menu()
        items = [('Submit', self.submit_link),
                 ('Copy URL', self.copy_link),
                 ('Copy Title', self.copy_title),
                 ('Remove', self.remove_link)]

        for idx, item in enumerate(items):
            title, callback = item
            menu.Append(idx, title)
            wx.EVT_MENU(menu, idx, callback)

        p = evt.GetPoint()
        h = self.out.GetSizeTuple()[1] + self.karma.GetSizeTuple()[1]
        p[1] += h

        self.links_lock.release()
        self.frame.PopupMenu(menu, p)
        menu.Destroy()
        

    def links_selected(self):
        i = -1
        selected = []
        while True:
            i = self.links.GetNextItem(i,
                                      wx.LIST_NEXT_ALL,
                                      wx.LIST_STATE_SELECTED)
            if i == -1:
                break

            selected.append(i)

        return selected

    def link_keypress(self, evt):
        self.links_lock.acquire()
        if evt.GetKeyCode() == 127: #delete
            for i in reversed(self.links_selected()):
                self.remove_link_idx(i)

        self.links_save()
        self.links_lock.release()

    def remove_link(self, evt):
        self.links_lock.acquire()
        i = self.menu_idx
        self.remove_link_idx(i)
        self.links_save()
        self.links_lock.release()

    def remove_link_idx(self, i):
        url = self.links.GetItem(i, 2).GetText()

        if url in self.links_queued:
            self.links_checked[url] = self.links_queued[url]
            del self.links_queued[url]

        self.links.DeleteItem(i)

    def submit_link(self, evt):
        i = self.menu_idx
        url = self.links.GetItem(i, 2).GetText()
        title = self.links.GetItem(i, 1).GetText()
        subreddit = self.links.GetItem(i, 3).GetText()

        submit_url = reddit.get_submit_url(url, title, subreddit)
        
        webbrowser.open_new_tab(submit_url)

    def copy_title(self, evt):
        i = self.menu_idx
        title = self.links.GetItem(i, 1).GetText()

        pyperclip.copy(title)

    def copy_link(self, evt):
        i = self.menu_idx
        url = self.links.GetItem(i, 2).GetText()

        pyperclip.copy(url)

    def links_activate(self, evt):
        i = evt.GetIndex()
        url = self.links.GetItem(i, 2).GetText()
        webbrowser.open_new_tab(url)

    def url_open(self, evt):
        m = evt.GetMouseEvent()
        s = evt.GetURLStart()
        e = evt.GetURLEnd()

        if m.LeftDown():
            self.url_next = self.out.GetRange(s, e)

    def url_open2(self, evt):
        if self.url_next is not None:
            webbrowser.open_new_tab(self.url_next)
            self.url_next = None

    def out_append(self, *args, **kwargs):
        wx.CallAfter(self.do_out_append, *args, **kwargs)

    def do_out_append(self, *args):
        self.out.SetInsertionPointEnd()
        self.out.WriteText(u' '.join(map(unicode, args)))
        self.out.SetInsertionPointEnd()
        
def serv_run():
    GUIMain()

if __name__ == '__main__':
    GUIMain()
