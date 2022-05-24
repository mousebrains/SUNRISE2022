#! /usr/bin/env python3
#
# Monitor when a file is updated using inotify
# then read in the updates and pour the results into a database
# and into a NetCDF file
#
# May-2022, Pat Welch, pat@mousebrains.com

from argparse import ArgumentParser
from TPWUtils import Logger
from TPWUtils import INotify
from TPWUtils import Thread
import logging

parser = ArgumentParser()
Logger.addArgs(parser)
args = parser.parse_args()

Logger.mkLogger(args)

logging.info("Args %s", args)
