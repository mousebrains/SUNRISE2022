#! /usr/bin/env python3
#
# Sync the data/Processed_NC/ADCP_UHDAS/*.nc to ~Sync and vice versa
#
# June-2022, Pat Welch, pat@mousebrains.com

from argparse import ArgumentParser
from TPWUtils import Logger
import logging
import subprocess
import glob
import socket
import os
import sys

def rsyncit(src:str, tgt:str, args:ArgumentParser) -> None:
    files = glob.glob(src)
    if not files:
        logging.info("No files found for %s", src)
        return

    if not os.path.isdir(tgt):
        logging.info("Creating %s", tgt)
        os.makedirs(tgt, mode=0o766, exists_ok=True)

    cmd = [
            args.rsync,
            "--archive",
            "--verbose",
            "--stats",
            ]
    cmd.extend(files)
    cmd.append(tgt)
    logging.info("Command %s", " ".join(cmd))
    s = subprocess.run(cmd, capture_output=True, shell=False)
    if s.returncode: logging.error("returncode %s", s.returncode)
    if s.stderr: logging.warning("stderr %s", str(s.stderr, "UTF-8"))
    if s.stdout: logging.info("stdout %s", str(s.stdout, "UTF-8"))

parser = ArgumentParser()
Logger.addArgs(parser)
parser.add_argument("--rsync", type=str, default="/usr/bin/rsync", help="rsync command")
parser.add_argument("--processed", type=str, default="/mnt/sci/data/Processed_NC/ADCP_UHDAS",
        help="Where nc files are stored on the science share")
parser.add_argument("--cruise", type=str, default="SUNRISE2022", help="Cruise prefix")
args = parser.parse_args()

Logger.mkLogger(args)

logging.info("Args %s", args)

hostname = socket.gethostname()

if "pe" in hostname:
    local = "PE"
    target = "Pelican"
    remote = "PointSur"
else:
    local = "PS"
    target = "PointSur"
    remote = "Pelican"

local = os.path.join(args.processed, args.cruise + "_" + local + "_*_concat.nc")
target = os.path.abspath(os.path.expanduser(os.path.join("~/Sync", target, "ADCP")))
remote = os.path.abspath(os.path.expanduser(os.path.join("~/Sync", remote, "ADCP")))

rsyncit(local, target, args) # From this host to sync
if os.path.isdir(remote):
    rsyncit(os.path.join(remote, args.cruise + "*.nc"), args.processed, args)

