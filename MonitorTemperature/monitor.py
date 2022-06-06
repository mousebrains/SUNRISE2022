#! /usr/bin/env python3
#
# Monitor the temperature of a system and send datagrams to shore with the information
#
# May-2021, Pat Welch, pat@mousebrains.com
# June-2022, Pat Welch, pat@mousebrains.com, rewritten

from argparse import ArgumentParser
from TPWUtils import Logger
import logging
from Hosts import Hosts, Host
import socket
import time
import os
import sys

def udpSend(host:str, port:int, data:bytes) -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        n = s.sendto(data, (host, port))
        logging.info("UDP %s:%s sent %s bytes of %s", host, port, n, data)
        return n

def tcpSend(host:str, port:int, data:bytes) -> int:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))
            n = s.send(data)
            logging.info("TCP %s:%s sent %s bytes of %s", host, port, n, data)
            return n
    except:
        logging.exception("Error sending %s to %s:%s", data, host, port)
        return None


def postData(args:ArgumentParser, host:Host) -> None:
    temp = None
    total = None
    free = None
    used = None

    try:
        info = os.statvfs(args.fs) # Get the filesystem information
        norm = info.f_frsize / 2**30 # tens of gigabytes
        total = info.f_blocks * norm
        free = info.f_bavail * norm
        avail = free / total # fraction available
        if os.path.isfile(args.tempDevice):
            with open(args.tempDevice, "r") as fp:
                temp = int(fp.read())# temperature in milliC
    except:
        logging.exception("Unexpected exception")

    if temp is None and total is None and free is None and avail is None:
        logging.warning("No temperature or space information found")
        return False
   
    logging.info("Temp %s total %s free %s GB %s%%", temp, total, free, avail*100)

    # Prepare the datagram
    data = bytearray()
    data+= host.signature()
    data+= host.encodeTemperature(temp)
    data+= host.encodeSpace(free)
    data+= host.encodeFraction(avail)
    data+= host.hostNumber()

    if args.tcp:
        tcpSend(args.host, args.port, data)
    else:
        udpSend(args.host, args.port, data)
        
parser = ArgumentParser()
Logger.addArgs(parser)
Hosts.addArgs(parser)
parser.add_argument("--tempDevice", type=str, default="/sys/class/thermal/thermal_zone0/temp", 
        help="Name of thermal device to read temperature from")
parser.add_argument("--tempNorm", type=float, default=0.1, help="milliC to centiC")
parser.add_argument("--spaceNorm", type=float, default=100, help="GB to 10MB")
parser.add_argument("--fs", type=str, default="/", help="Filesystem to send information about")
parser.add_argument("--dt", type=float, default=600, help="Time between samples in seconds")
parser.add_argument("--host", type=str, required=True, help="Hostname to send datagrams to")
parser.add_argument("--port", type=int, default=11113, help="port to send datagrams to")
grp = parser.add_mutually_exclusive_group()
grp.add_argument("--tcp", action="store_true", help="Connect using TCP")
grp.add_argument("--udp", action="store_true", help="Connect using UDP datagrams")
args = parser.parse_args()

Logger.mkLogger(args, fmt="%(asctime)s %(levelname)s: %(message)s")

try:
    host = Hosts(args).getHost()
    if host is None:
        sys.exit(1)

    while True:
        now = time.time()
        postData(args, host)
        logging.info("Sleeping for %s seconds", args.dt)
        nxt = now + args.dt
        time.sleep(max(0.1, nxt - time.time()))
except:
    logging.exception("Unexpected exception")
