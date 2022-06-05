#! /usr/bin/env python3
#
# Read in hosts.yaml for conversions
#
# June-2022, Pat Welch, pat@mousebrains.com

import yaml
import json
import logging
import socket
import os
from argparse import ArgumentParser

class Host:
    __signature = b"\xd2\x93" # 2 byte message prefix

    def __init__(self, name:str, info:dict) -> None:
        self.__name = name
        self.__hostNumber = info["number"].to_bytes(1, byteorder="big", signed=False)
        self.__spaceNorm  = info["spaceNorm"]
        self.__tempNorm   = info["tempNorm"]

    def host(self) -> str:
        return self.__name

    def hostNumber(self) -> bytes:
        return self.__hostNumber

    @classmethod
    def signature(cls) -> bytes:
        return cls.__signature

    @classmethod
    def checkSignature(cls, val:bytes) -> bool:
        return val == cls.__signature

    @staticmethod
    def encode(val:float, norm:float, tit:str) -> bytes:
        if val is None: return (0xffff).to_bytes(2, byteorder="big", signed=False)
        a = int(round(val * norm))
        if a < 0:
            logging.error("Normalized %s, %s, is less than zero, %s, %s", tit, a, val, norm)
            a = 0
        elif a > 65536:
            logging.error("Normalized %s, %s, is >65536, %s, %s", tit, a, val, norm)
            a = 65536
        return a.to_bytes(2, byteorder="big", signed=False)

    def encodeSpace(self, sz:float) -> bytes:
        return self.encode(sz, self.__spaceNorm, "space")

    def encodeTemperature(self, temperature:float) -> bytes:
        return self.encode(temperature, self.__tempNorm, "temperature")

    def encodeFraction(self, frac:float) -> bytes:
        return self.encode(frac, 0xffff, "Fraction")

    @staticmethod
    def decode(val:bytes, norm:float=None) -> float:
        a = int.from_bytes(val, byteorder="big", signed=False)
        if a == 0xffff: return None
        if norm is None: return a
        return float(a) / norm

    def decodeSpace(self, sz:bytes) -> float:
        return self.decode(sz, self.__spaceNorm)

    def decodeTemperature(self, val:bytes) -> float:
        return self.decode(val, self.__tempNorm)

    def decodeFraction(self, val:bytes) -> float:
        return self.decode(val, 0xffff)

class Hosts:
    def __init__(self, args:ArgumentParser) -> None:
        fn = args.hostsYAML
        self.__filename = fn
        if not os.path.isfile(fn):
            logging.error("%s does not exist", fn)
            info = {}
        else:
            with open(fn, "r") as fp: 
                info = yaml.safe_load(fp)

        logging.debug("%s ->\n%s", fn, json.dumps(info, indent=4, sort_keys=True))

        self.__number2host = {}
        self.__info = {}

        for key in info:
            host = Host(key, info[key])
            self.__info[key] = host
            self.__number2host[host.hostNumber()] = host


    @staticmethod
    def addArgs(parser:ArgumentParser):
        parser.add_argument("--hostsYAML", type=str, default="hosts.yaml",
                help="Hostname configuration file")

    @staticmethod
    def checkSignature(val:bytes) -> bool:
        return Host.checkSignature(val)

    def getHost(self, hostname:str=socket.gethostname()) -> Host:
        if hostname in self.__info:
            return self.__info[hostname]

        logging.error("Host, %s, not in %s", hostname, self.__filename)
        return None

    def hostFromNumber(self, hostNumber:bytes) -> Host:
        return self.__number2host[hostNumber] if hostNumber in self.__number2host else None
