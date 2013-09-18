import time

from guiclient import new_rpc

class KarmaFeed:
    def watch(self):
        rpc = new_rpc('Link Karma')

        link_karma = -1
        while True:
            new_link_karma = rpc.gui_karma_get()

            if link_karma != new_link_karma:
                link_karma = new_link_karma
                rpc.gui_karma_set(link_karma)
                print link_karma
            time.sleep(35)
