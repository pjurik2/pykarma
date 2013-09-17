import multiprocessing
import time


from feeds import *
import gui

if __name__ == '__main__':
    p = multiprocessing.Process(target=gui.serv_run)
    p.start()
    time.sleep(5)

    feeds = (
                #hn.HackerNewsFeed(),
                gnews.GoogleNewsFeed(),
                karma.KarmaFeed(),
                ars.ArsTechnicaFeed(),
                physorg.PhysorgFeed(),
                reuters.ReutersFeed(),
                bbc.BBCFeed(),
                torrentfreak.TorrentfreakFeed(),
            )

    processes = [multiprocessing.Process(target=f.watch) for f in feeds]

    for p in processes:
        p.start()

    for p in processes:
        print p.pid, p._target.__name__

    while True:
        time.sleep(60)
