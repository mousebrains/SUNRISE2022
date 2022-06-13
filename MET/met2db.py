#! /usr/bin/env python3
#
# Monitor a directory for a changing MET CSV file
#
# June-2022, Pat Welch, pat@mousebrains.com

from argparse import ArgumentParser
from Config import Config
from DB import DB
import Monitor
from TPWUtils.Thread import Thread
from TPWUtils import Logger
import logging
from TPWUtils.INotify import INotify
import pyinotify
import psycopg2
import queue

parser = ArgumentParser()
Logger.addArgs(parser)
Config.addArgs(parser)
DB.addArgs(parser)
parser.add_argument("--directory", type=str, required=True, help="Name of directory to monitor")
grp = parser.add_mutually_exclusive_group(required=True)
grp.add_argument("--inotify", action="store_true",
        help="Use INotify to monitor changes in a directory")
grp.add_argument("--polling", action="store_true",
        help="Poll for changes in a directory's contents")
args = parser.parse_args()

Logger.mkLogger(args)
logging.info("Args %s", args)

try:
    config = Config(args)

    if args.inotify: # Use inotify
        i = INotify(args, flags=pyinotify.IN_CLOSE_WRITE | pyinotify.IN_MOVED_TO)
        monitor = Monitor.MonitorINotify(args, i.queue, config)
        i.start()
        i.addTree(args.directory)
    else: # Use polling
        monitor = Monitor.MonitorPolling(args, config)

    db = DB(args, monitor, config)

    monitor.start()
    db.start()


    Thread.waitForException()
except:
    logging.exception("Unexpected exception")
