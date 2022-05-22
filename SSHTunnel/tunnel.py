#! /usr/bin/env python3
#
# Build a ssh connection to a target and add a tunnel back to my local ssh port
#
# This is intended to be run as a service, so it will auto-restart when the connection
# fails and the script exits with zero
# 
# Jan-2022, Pat Welch, pat@mousebrains.com

from argparse import ArgumentParser
import socket
import yaml
import subprocess
import time
import sys
import re
import os.path
from TPWUtils import Logger

def loadYAML(fn:str) -> list:
    if not os.path.isfile(fn):
        logger.error("%s does not exist", fn)
        sys.exit(1)
    with open(fn, "r") as fp: info = yaml.safe_load(fp)
    hostname = socket.gethostname()
    if hostname not in info:
        logger.error("Hostname, %s, not in information from %s", hostname, fn)
        sys.exit(1)
    logger.info("Hostname %s", hostname)
    items = []
    for i in range(len(info[hostname])):
        item = info[hostname][i]
        if not re.match("\d+:localhost:\d+", item):
            logger.error("Incorrectly formated item, %s, for hostname %s in %s", 
                    item, hostname, fn)
            sys.exit(1)
        items.extend(["-R", item])
    return items

parser = ArgumentParser()
Logger.addArgs(parser)
parser.add_argument("--config", type=str, default="hostnames.yaml",
        help="Hostname to ports to forward YAML file")

grp = parser.add_argument_group(description="SSH related options")
grp.add_argument("--ssh", type=str, default="/usr/bin/ssh", help="SSH binary to use")
grp.add_argument("--interval", type=int, default=60, help="Value to set ServerAliveInterval to")
grp.add_argument("--count", type=int, default=3, help="Value to set ServerAliveCountMax to")
grp.add_argument("--identity", type=str, help="Public key filename")
grp.add_argument("--username", type=str, help="Remote username")
grp.add_argument("--host", type=str, required=True, help="Remote hostname")
grp.add_argument("--port", type=int, help="Remote host port to connect to")
args = parser.parse_args()

logger = Logger.mkLogger(args)

info = loadYAML(args.config)

cmd = [args.ssh, "-N", "-x", "-T"]

if args.identity:
    cmd.extend(("-i", args.identity))

if args.interval > 0:
    cmd.extend(("-o", f"ServerAliveInterval={args.interval}"))
    if args.count > 0:
        cmd.extend(("-o", f"ServerAliveCountMax={args.count}"))

if args.username:
    cmd.extend(("-l", args.username))

if args.port:
    cmd.extend(("-p", args.port))

cmd.extend(info)

cmd.append(args.host)

logger.info("Command: %s", " ".join(cmd))
try:
    s = subprocess.run(cmd, capture_output=True, shell=False)
    logger.warning("\n%s", s)
except:
    logger.exception("Error in %s", cmd)
    sys.exit(0)
