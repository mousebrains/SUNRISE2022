#! /usr/bin/env python3
#
# Syncing the ADCP files to/from a ship
#
# June-2022, Pat Welch, pat@mousebrains.com

from argparse import ArgumentParser
from TPWUtils import Logger
import logging
import subprocess
import glob
import os
import sys

parser = ArgumentParser()
Logger.addArgs(parser)
parser.add_argument("--rsync", type=str, default="/usr/bin/rsync", help="rsync command")
parser.add_argument("--adcpdir", type=str, default="/mnt/adcp",
        help="Where the UHDAS data is stored")
parser.add_argument("--datadir", type=str, default="/mnt/sci/data",
        help="Where the science data is stored")
parser.add_argument("--pattern", type=str, required=True, help="Directory name glob pattern")
parser.add_argument("--platform", type=str, help="Two letter prefix for this platform")
args = parser.parse_args()

Logger.mkLogger(args)

if args.platform is None:
    args.platform = args.pattern[:2]

logging.info("Args %s", args)

cmd = [
    args.rsync,
    "--archive",
    "--stats",
    ]
cmd.extend(glob.glob(os.path.join(args.adcpdir,args.pattern + "*")))
cmd.append(os.path.join(args.datadir, "Platform",  args.platform, "ADCP_UHDAS"))
s = subprocess.run(cmd, capture_output=True, shell=False)
if s.returncode: logging.error("returncode %s", s.returncode)
if s.stderr: logging.warning("stderr %s", str(s.stderr, "UTF-8"))
if s.stdout: logging.info("stdout %s", str(s.stdout, "UTF-8"))
