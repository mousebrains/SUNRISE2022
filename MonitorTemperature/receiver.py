#! /usr/bin/env python3
#
# Listen to a socket for a datagram with status information about the ship board computers
#
# May-2021, Pat Welch, pat@mousebrains.com
# June-2022, Pat Welch, pat@mousebrains.com, rewritten

from argparse import ArgumentParser
import queue
import psycopg2 # Postgresql interface
import socket
from TPWUtils import Thread
import threading
from TPWUtils import Logger
from DataPacket import Packet
from Hosts import Hosts
import time
import logging
import os.path

class Reader(Thread.Thread):
    ''' Common components for reading data packets '''
    def __init__(self, name:str, args:ArgumentParser) -> None:
        Thread.Thread.__init__(self, name, args)
        self.hosts = Hosts(args)
        self.packet = Packet(args)
        self.queues = []

    @staticmethod
    def addArgs(parser:ArgumentParser) -> None:
        Hosts.addArgs(parser)
        grp = parser.add_argument_group(description="TCP/UDP listener options")
        grp.add_argument('--port', type=int, default=11113, metavar='port',
                help='Port to listen on')
        grp.add_argument("--size", type=int, default=8, help="Datagram size, power of 2 >= 8")
        grp = grp.add_mutually_exclusive_group()
        grp.add_argument("--tcp", action="store_true", help="Connect using TCP")
        grp.add_argument("--udp", action="store_true", help="Connect using UDP datagrams")

    def addQueue(self, q:queue.Queue) -> None:
        self.queues.append(q)

    def received(self, data:bytes, addr:tuple) -> None:
        now = time.time()
        (host, temp, free, frac) = self.packet.explode(data, self.hosts)
        if host is not None:
            payload = (now, addr[0], addr[1], host, temp, free, frac)
            logging.debug("Payload %s", payload)
            for q in self.queues: q.put(payload)
        else:
            logging.debug("data %s", data)

class ConsumeTCP(Thread.Thread):
    ''' Consume a TCP connection '''
    def __init__(self, args:ArgumentParser, connection, addr:tuple, rdr:Reader) -> None:
        Thread.Thread.__init__(self, f"TCP:{addr[0]}:{addr[1]}", args)
        self.__connection = connection
        self.__addr = addr
        self.__reader = rdr

    def runIt(self) -> None: # Called on thread start
        sz = self.args.size
        rdr = self.__reader
        addr = self.__addr
        try:
            with self.__connection as conn:
                while True:
                    data = conn.recv(sz)
                    if not data: break
                    rdr.received(data, addr)
        except:
            logging.exception("Connection problem")

class ReaderTCP(Reader):
    ''' Wait on a connection request, then spawn off a TCP consumer '''
    def __init__(self, args:ArgumentParser) -> None:
        Reader.__init__(self, "RdrTCP", args)

    @staticmethod
    def addArgs(parser:ArgumentParser) -> None:
        grp = parser.add_argument_group(description="TCP listener options")
        grp.add_argument("--nThreads", type=int, default=30,
                help="Maximum number of simultaneous connections")

    def runIt(self) -> None: # Called on thread start
        args = self.args
        port = args.port
        sz = args.size
        maxThreads = args.nThreads
        logging.info("Starting port %s size %s", port, sz)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', port))
            s.listen() # Listen for incoming TCP connections
            logging.debug("Listening to port %s", port)
            while True:
                (conn, addr) = s.accept() # Got a connection request, so spin it off
                if threading.active_count() > maxThreads:
                    logging.info("Rejecting connections %s due to maximum number of threads, %s<%s",
                            addr, maxThreads, threading.active_count())
                    conn = None # Close the connection, eventually
                else:
                    thrd = ConsumeTCP(args, conn, addr, self)
                    thrd.start()
  
class ReaderUDP(Reader):
    ''' Wait for UDP datagrams '''
    def __init__(self, args:ArgumentParser) -> None:
        Reader.__init__(self, "RdrUDP", args)

    @staticmethod
    def addArgs(parser:ArgumentParser) -> None:
        pass

    def runIt(self) -> None: # Called on thread start
        args = self.args
        port = args.port
        sz = args.size
        logging.info("Starting port %s size %s", port, sz)
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.bind(("", port))
            while True:
                (data, addr) = s.recvfrom(sz)
                self.received(data, addr)

class Writer(Thread.Thread):
    ''' Wait on a queue, and write the item to a database '''
    def __init__(self, args:ArgumentParser, rdr:Reader) -> None:
        Thread.Thread.__init__(self, "Writer", args)
        self.__queue = queue.Queue()
        rdr.addQueue(self.__queue)

    @staticmethod
    def addArgs(parser:ArgumentParser) -> None:
        grp = parser.add_argument_group(description="Database writer options")
        grp.add_argument("--table", type=str, default="status", metavar="tblName",
                help="Postgresql table name")
        grp.add_argument("--db", type=str, metavar="dbName",
                help="Postgresql database name")

    def mkTable(self, cur) -> None:
        tbl = self.args.table
        sql = "CREATE TABLE IF NOT EXISTS " + tbl + "(\n"
        sql+= " t REAL, -- Time datagram was received\n"
        sql+= " ipAddr TEXT, -- IP address datagram received from\n"
        sql+= " port INTEGER, -- port number datagram received on\n"
        sql+= " host TEXT, -- Hostname\n"
        sql+= " temp REAL, -- Temperature (C)\n"
        sql+= " free REAL, -- GB available\n"
        sql+= " avail REAL, -- Fraction available\n"
        sql+= " PRIMARY KEY(t, host)\n"
        sql+= " );"
        cur.execute(sql)

    def runIt(self) -> None: # Called on thread start
        args = self.args
        q = self.__queue
        sql = "INSERT INTO " + args.table + " VALUES(%s,%s,%s,%s,%s,%s,%s);"
        dbName = f"dbname={args.db}"
        logging.info("Starting SQL\n%s", sql)
        qMakeTable = True
        while True: # Loop forever
            row = q.get()
            q.task_done()
            (t, addr, port, host, temp, free, avail) = row
            logging.info("Received %s temp %s free %s avail %s", host, temp, free, avail)
            with psycopg2.connect(dbName) as db:
                cur = db.cursor()
                cur.execute("BEGIN;")
                if qMakeTable:
                    self.mkTable(cur)
                    qMakeTable = False
                cur.execute(sql, row)
                cur.execute("COMMIT;")

class CSV(Thread.Thread):
    ''' Wait on a queue to look at a database and update a CSV file '''
    def __init__(self, args:ArgumentParser, rdr:Reader) -> None:
        Thread.Thread.__init__(self, "CSV", args)
        self.__queue = queue.Queue()
        rdr.addQueue(self.__queue)

    @staticmethod
    def addArgs(parser:ArgumentParser) -> None:
        parser.add_argument("--csv", type=str, help="CSV filename")

    def runIt(self) -> None: # Called on thread start
        args = self.args
        fn = args.csv
        q = self.__queue
        logging.info("Starting %s", fn)
        if not os.path.isfile(fn):
            with open(fn, "w") as fp:
                fp.write(",".join(("t", "host", "temp", "free", "avail")) + "\n")

        while True:
            row = q.get()
            q.task_done()
            (t, addr, port, host, temp, free, avail) = row
            logging.info("Received %s temp %s free %s avail %s", host, temp, free, avail)
            payload = (
                    str(t),
                    host,
                    "" if temp is None else str(temp),
                    "" if free is None else str(free),
                    "" if avail is None else str(avail),
                    )
            with open(fn, "a") as fp:
                fp.write(",".join(payload) + "\n")

parser = ArgumentParser(description="Listen for a LiveGPS message")
Logger.addArgs(parser)
Reader.addArgs(parser)
ReaderTCP.addArgs(parser)
ReaderUDP.addArgs(parser)
Writer.addArgs(parser)
CSV.addArgs(parser)
args = parser.parse_args()

Logger.mkLogger(args)
logging.info("args=%s", args)

try:
    reader = ReaderTCP(args) if args.tcp else ReaderUDP(args)
    if args.db: 
        writer = Writer(args, reader) # Create the db writer thread
        writer.start()
    if args.csv: 
        csv = CSV(args, reader) # Create the CSV file
        csv.start()

    reader.start() # Start the reader thread

    Thread.Thread.waitForException() # This will only raise an exception from a thread
except:
    logging.exception("Unexpected exception while listening")
