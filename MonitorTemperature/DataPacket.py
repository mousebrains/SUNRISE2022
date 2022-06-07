#! /usr/bin/env python3
#
# Collect information from the system and prepare a data packet to be sent to another system.
#
# This was originally designed for UDP datagrams, so the data packet is small with
# data integrity built in, but no error correction.
#
# The host specific configuration information is in a YAML file.
#
# June-2022, Pat Welch, pat@mousebrains.com

from argparse import ArgumentParser
from Hosts import Hosts, Host
from Hash import hash8, hash8Integer
import logging
import socket
import os

class Packet:
    def __init__(self, args:ArgumentParser) -> None:
        self.__args = args

    @staticmethod
    def addArgs(parser:ArgumentParser) -> None:
        grp = parser.add_argument_group("Data packet related options")
        grp.add_argument("--tempDevice", type=str, default="/sys/class/thermal/thermal_zone0/temp",
                help="Name of thermal device to read temperature from")
        grp.add_argument("--fs", type=str, default="/", 
                help="Filesystem to send information about")

    def implode(self, host:Host) -> bytes:
        temp = None
        total = None
        free = None
        try:
            args = self.__args
            # First collect file system information
            info = os.statvfs(args.fs) # Get the filesystem information
            norm = info.f_frsize / 2**30 # tens of gigabytes
            total = info.f_blocks * norm
            free = info.f_bavail * norm
            if os.path.isfile(args.tempDevice):
                with open(args.tempDevice, "r") as fp:
                    temp = int(fp.read())# temperature in milliC
        except:
            logging.exception("Unexpected exception")
            return None

        data = bytearray()
        data+= host.hostNumber
        data+= host.encodeTemperature(temp)
        data+= host.encodeSpace(free)
        data+= host.encodeFraction(free, total)
        data+= hash8(data)
        return data

    def explode(self, data:bytes, hosts:Hosts) -> tuple[str, float, float, float]:
        if len(data) != 8:
            logging.warning("Data packet, %s, not 8 bytes long, %s", len(data), data)
            return (None, None, None, None)
        hash = hash8Integer(data[:-1])
        if hash != data[-1]:
            logging.warning("Data packet hash, %s, does not agree with calculation, %s, for %s",
                    data[-1], hash, data)
            return (None, None, None, None)

        host = hosts.hostFromNumber(data[0])
        if host is None:
            return (None, None, None, None)
        return (
                host.name,
                host.decodeTemperature(data[1:3]),
                host.decodeSpace(data[3:5]),
                host.decodeFraction(data[5:7]),
                )

if __name__ == "__main__":
    parser = ArgumentParser()
    Packet.addArgs(parser)
    Hosts.addArgs(parser)
    args = parser.parse_args()

    hosts = Hosts(args)
    host = hosts.getHost()
    packet = Packet(args)
    data = packet.implode(host)
    print("Packet", data, len(data))
    (host, temp, free, frac) = packet.explode(data, hosts)
    print("Host", host, "temp", temp, "free", free, "frac", frac)
