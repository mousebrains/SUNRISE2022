#! /usr/bin/env python3
#
# Monitor a directory for a changing MET CSV file
# using either inotify or polling
#
# June-2022, Pat Welch, pat@mousebrains.com

from argparse import ArgumentParser
from TPWUtils.Thread import Thread
from TPWUtils import Logger
import logging
from TPWUtils.INotify import INotify
import pyinotify
import queue
import re
import os
import time
import sys

class Monitor(Thread):
    def __init__(self, name:str, args:ArgumentParser):
        Thread.__init__(self, name, args)
        self.__queues = [] # Where to send filenames to
        self.pattern = re.compile(args.pattern)
        # Seconds after an update before starting any actions
        self.dt = args.dt

    def __repr__(self) -> str:
        return f"dt={self.dt} pattern={self.pattern}"

    def addQueue(self, queue:queue.Queue) -> None:
        self.__queues.append(queue)

    def send(self, fn:str) -> None:
        logging.debug("Sending %s", fn)
        for q in self.__queues: q.put(fn)

class MonitorINotify(Monitor):
    def __init__(self, args:ArgumentParser, queue:queue.Queue) -> None:
        Monitor.__init__(self, "Mon", args)
        self.__qIn = queue

    def runIt(self) -> None: # Called on thread start
        dt = self.dt
        q = self.__qIn
        pattern = self.pattern
        logging.info("Starting %s", self)
        pending = {}
        tNext = None
        while True:
            try:
                (t, fn) = q.get(timeout=None if tNext is None else max(0.1, tNext - time.time()))
                q.task_done()
                if pattern and not pattern.match(os.path.basename(fn)): continue
                if fn not in pending:
                    logging.debug("Adding %s", fn)
                    pending[fn] = t + dt
                    tNext = t if tNext is None else min(tNext, pending[fn])
            except queue.Empty: # Timed out, so see which files need to have notifications sent
                now = time.time() + 0.1
                toDrop = set()
                tNext = None
                for fn in pending: 
                    if pending[fn] <= now:
                        toDrop.add(fn)
                    elif tNext is None:
                        tNext = pending[fn]
                    else:
                        tNext = min(pending[fn], tNext)

                for fn in toDrop: 
                    del pending[fn]
                    self.send(fn)

class MonitorPolling(Monitor):
    def __init__(self, args:ArgumentParser, dirname:str) -> None:
        Monitor.__init__(self, "Poll", args)
        self.__directory = dirname

    def runIt(self) -> None: # Called on thread start
        dt = self.dt
        dirname = os.path.abspath(os.path.expanduser(self.__directory))
        pattern = self.pattern
        logging.info("Starting %s", self)
        mtimes = {}
        sizes = {}
        tPrev = time.time()
        while True:
            toSend = {}
            for item in os.scandir(dirname):
                if item.is_dir(): continue # Skip directories
                fn = item.name
                if pattern and not pattern.match(fn): continue
                istat = item.stat()
                mtime = istat.st_mtime
                sz = istat.st_size
                if fn in mtimes and mtimes[fn] == mtime and sizes[fn] == sz: continue # no change
                mtimes[fn] = mtime
                sizes[fn] = sz
                tNext = mtime + dt
                if tNext not in toSend: toSend[tNext] = []
                toSend[tNext].append(item.path)
            for tNext in sorted(toSend): # Walk through in time order
                tWait = max(0.01, tNext - time.time())
                logging.debug("tNext %s tWait %s fn %s", tNext, tWait, toSend[tNext])
                time.sleep(tWait) # Wait until tNext
                for fn in toSend[tNext]: self.send(fn)

            tNext = tPrev + dt
            tWait = max(0.01, tNext - time.time())
            logging.debug("Waiting for %s seconds", tWait)
            time.sleep(tWait)
            tPrev = time.time()

if __name__ == "__main__":
    parser = ArgumentParser()
    Logger.addArgs(parser)
    parser.add_argument("--directory", type=str, required=True, help="Name of directory to monitor")
    parser.add_argument("--dt", type=float, default=120, help="Seconds to wait after update")
    parser.add_argument("--pattern", type=str, default=r"RHIB_status_GS3_UBOX\d+_\w+_\d+_\d+.txt",
            help="Filename pattern to match")
    grp = parser.add_mutually_exclusive_group(required=True)
    grp.add_argument("--inotify", action="store_true",
            help="Use INotify to monitor changes in a directory")
    grp.add_argument("--polling", action="store_true",
            help="Poll for changes in a directory's contents")
    args = parser.parse_args()

    Logger.mkLogger(args)
    logging.info("Args %s", args)

    try:
        if args.inotify: # Use inotify
            i = INotify(args, flags=pyinotify.IN_CLOSE_WRITE | pyinotify.IN_MOVED_TO)
            monitor = MonitorINotify(args, i.queue)
            i.start()
            i.addTree(args.directory)
        else: # Use polling
            monitor = MonitorPolling(args, args.directory)

        monitor.start()
        Thread.waitForException()
    except:
        logging.exception("Unexpected exception")
