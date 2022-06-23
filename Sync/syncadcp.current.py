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
        os.makedirs(tgt, mode=0o766, exist_ok=True)

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
parser.add_argument("--platform", type=str, default="/mnt/sci/data/Platform",
        help="Where proc/*/contour files are stored on the science share")
parser.add_argument("--adcp", type=str, default="/mnt/adcp/current_cruise/proc",
        help="Where the UHDAS current cruise files are")
args = parser.parse_args()

Logger.mkLogger(args)

logging.info("Args %s", args)

hostname = socket.gethostname()

if "pe" in hostname:
    platform = "PE"
else:
    platform = "PS"

for src in glob.glob(os.path.join(args.adcp, "*")):
    adcp = os.path.basename(src)
    tgt = os.path.join(args.platform, platform, "ADCP_UHDAS", adcp)
    logging.info("adcp %s %s", src, tgt)
    rsyncit(os.path.join(src, "contour") + "/", tgt, args) # From this host to sync
