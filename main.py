import multiprocessing
import time


from feeds import *
import gui

if __name__ == '__main__':
    p = multiprocessing.Process(target=gui.serv_run)
    p.start()
    time.sleep(5)

    functions = (
##                 hn.hn_watch,
##                 gnews.gnews_watch,
##                 count.count_watch,
##                 ars.ars_watch,
##                 physorg.physorg_watch,
##                 reuters.reuters_watch,
##                 bbc.bbc_watch,
##                 torrentfreak.torrentfreak_watch,
                 )

    processes = [multiprocessing.Process(target=f) for f in functions]

    for p in processes:
        p.start()

    for p in processes:
        print p.pid, p._target.__name__

    while True:
        time.sleep(60)
