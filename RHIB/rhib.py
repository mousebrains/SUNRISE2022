#! /usr/bin/env python3
#
# Parse RHIB files
#
# July-2022, Pat Welch, pat@mousebrains.com

from TPWUtils.Thread import Thread
import logging
import re
import datetime
import numpy as np
import sys

class RHIB_Parser:
    def __init__(self) -> None:
        prefix = b"^\d{2}-\w+-\d{4} \d{2}:\d{2}:\d{2} UBOX(\d{2}) -- (\w+) -- "
        prefix+= b"(\d{4})/(\d{2})/(\d{2}) (\d{2}):(\d{2}):(\d{2}) UTC -- (.+)"
        self.__prefix = re.compile(prefix)

        navinfo = b"LAT ([+-]?\d+[.]\d+)"
        navinfo+= b" LON ([+-]?\d+[.]\d+)"
        self.__navregex = re.compile(navinfo)

        keelctd = b"KDATE (\d{4})-(\d{2})-(\d{2})"
        keelctd+= b" KTIME (\d{2}):(\d{2}):(\d{2})[.](\d{3})"
        keelctd+= b" Temp\s+([+-]?\d+[.]\d*)"
        keelctd+= b" Sal\s+([+-]?\d+[.]\d*)"
        self.__keelctdregex = re.compile(keelctd)

        adcp = b"ADATE (\d{4})(\d{2})(\d{2})"
        adcp+= b" ATIME (\d{2})(\d{2})(\d{2})"
        adcp+= b" u ([+-]?\d+[.]\d+(?:,[+-]?\d+[.]\d+)*)"
        adcp+= b" v ([+-]?\d+[.]\d+(?:,[+-]?\d+[.]\d+)*)"
        adcp+= b" w ([+-]?\d+[.]\d+(?:,[+-]?\d+[.]\d+)*)"
        self.__adcpregex = re.compile(adcp)

    def __navinfo(self, box:int, t:datetime.datetime, tail:bytes, line:bytes) -> None:
        info = self.__navregex.match(tail)
        if not info:
            logging.info("NAVINFO failure %s", bytes(line))
            return
        lat = float(info[1])
        lon = float(info[2])
        logging.info("LAT %s LON %s", lat, lon)

    def __keelctd(self, box:int, t:datetime.datetime, tail:bytes, line:bytes) -> None:
        info = self.__keelctdregex.match(tail)
        if not info:
            logging.info("KEELCTD failure %s", bytes(line))
            return
        t = datetime.datetime(
                int(info[1]), int(info[2]), int(info[3]),
                int(info[4]), int(info[5]), int(info[6]),
                int(info[7]) * 1000,
                tzinfo=datetime.timezone.utc)
        temp = float(info[8])
        SP = float(info[9])
        logging.info("CTD %s T %s SP %s", t, temp, SP)

    def __adcp(self, box:int, t:datetime.datetime, tail:bytes, line:bytes) -> None:
        info = self.__adcpregex.match(tail)
        if not info:
            logging.info("ADCP failure %s", bytes(line))
            return
        t = datetime.datetime(
                int(info[1]), int(info[2]), int(info[3]),
                int(info[4]), int(info[5]), int(info[6]),
                tzinfo=datetime.timezone.utc)
        logging.info("ADCP t %s", t)
        u = np.array(str(info[7], "UTF-8").split(",")).astype(float)
        v = np.array(str(info[8], "UTF-8").split(",")).astype(float)
        w = np.array(str(info[9], "UTF-8").split(",")).astype(float)
        if u.size == v.size and u.size == w.size:
            logging.info("ADCP u %s", u)
            logging.info("ADCP v %s", v)
            logging.info("ADCP w %s", w)

    def __parseLines(self, buffer:bytearray) -> bytearray:
        parsers = {
                "navinfo": self.__navinfo,
                "keelctd": self.__keelctd,
                "adcp": self.__adcp,
                "winchstatus": None,
                "pdbinfo": None,
                "param": None,
                "wpcount": None,
                "curwp": None,
                "waypt": None,
                }
        offset = 0
        while True:
            index = buffer.find(b"\n", offset)
            if index < 0: break
            line = buffer[offset:index]
            offset = index + 1
            prefix = self.__prefix.match(line)
            if not prefix:
                logging.debug("Unrecognized line %s", bytes(line))
                continue
            box = int(prefix[1])
            ident = str(prefix[2], "UTF-8")
            t = datetime.datetime(
                    int(prefix[3]), int(prefix[4]), int(prefix[5]),
                    int(prefix[6]), int(prefix[7]), int(prefix[8]),
                    tzinfo=datetime.timezone.utc)
            tail = prefix[9]
            if ident in parsers:
                if parsers[ident]:
                    parsers[ident](box, t, tail, line)
            else:
                logging.debug("Unrecognized id %s line %s", ident, bytes(line))

        return buffer[offset:]

    def parseFile(self, fn:str, spos:int, cursor) -> int:
        with open(fn, "rb") as fp:
            if spos and spos > 0:
                logging.info("Seeking to %s in %s", spos, fn)
                fp.seek(spos - 1)
            buffer = bytearray()
            while True:
                content = fp.read(1024*1024) # Read in a chunk of the file
                if not content:
                    logging.info("EOF in %s", fn)
                    break
                buffer += content
                buffer = self.__parseLines(buffer)
                break
            return fp.tell() - len(buffer)

if __name__ == "__main__":
    from argparse import ArgumentParser
    from TPWUtils import Logger

    parser = ArgumentParser()
    Logger.addArgs(parser)
    parser.add_argument("--position", type=int, help="Position to start in the file")
    parser.add_argument("fn", nargs="+", type=str, help="Files to process")
    args = parser.parse_args()

    Logger.mkLogger(args, fmt="%(asctime)s %(levelname)s: %(message)s")

    rhib = RHIB_Parser()

    for fn in args.fn:
        logging.info("Working on %s", fn)
        pos = rhib.parseFile(fn, args.position, None)
        logging.info("%s pos %s", fn, pos)
