#! /usr/bin/env python3
#
# Monitor the temperature of a system and send datagrams to shore with the information
#
# May-2021, Pat Welch, pat@mousebrains.com
# June-2022, Pat Welch, pat@mousebrains.com, rewritten

from argparse import ArgumentParser
from TPWUtils import Logger
import logging
from DataPacket import Packet
from Hosts import Hosts, Host
import time
import socket
import sys

def doitUDP(args:ArgumentParser, host:Host, packet:Packet):
    while True:
        now = time.time()
        data = packet.implode(host)
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            n = s.sendto(data, (args.host, args.port))
            if n != len(data):
                logging.warning("UDP only sent %s bytes of %s for %s", n, len(data), data)
            else:
                logging.info("UDP %s:%s sent %s bytes of %s", args.host, args.port, n, data)
        nxt = now + args.dt
        time.sleep(max(0.1, nxt - time.time()))

def doitTCP(args:ArgumentParser, host:Host, packet:Packet):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((args.host, args.port))
        while True:
            now = time.time()
            data = packet.implode(host)
            n = s.send(data)
            if n != len(data):
                logging.warning("TCP only sent %s bytes of %s for %s", n, len(data), data)
            else:
                logging.info("TCP %s:%s sent %s bytes of %s", args.host, args.port, n, data)
            nxt = now + args.dt
            time.sleep(max(0.1, nxt - time.time()))

parser = ArgumentParser()
Logger.addArgs(parser)
Hosts.addArgs(parser)
Packet.addArgs(parser)
parser.add_argument("--dt", type=float, default=600, help="Time between samples in seconds")
parser.add_argument("--host", type=str, required=True, help="Hostname to send datagrams to")
parser.add_argument("--port", type=int, default=11113, help="port to send datagrams to")
grp = parser.add_mutually_exclusive_group(required=True)
grp.add_argument("--tcp", action="store_true", help="Send data using TCP packets")
grp.add_argument("--udp", action="store_true", help="Send data using UDP datagrams")
args = parser.parse_args()

Logger.mkLogger(args, fmt="%(asctime)s %(levelname)s: %(message)s")

try:
    host = Hosts(args).getHost()
    if host is None:
        sys.exit(1)

    packet = Packet(args)

    if args.tcp:
        doitTCP(args, host, packet)
    else:
        doitUDP(args, host, packet)
except:
    logging.exception("Unexpected exception")
