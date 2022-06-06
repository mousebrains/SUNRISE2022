#! /usr/bin/env python3
#
# Listen to a socket for a datagram with status information about the ship board computers
#
# May-2021, Pat Welch, pat@mousebrains.com
# June-2022, Pat Welch, pat@mousebrains.com, rewritten

from argparse import ArgumentParser
import queue
import psycopg2 # Postgresql interface
import sqlite3
import socket
from TPWUtils import Thread
from TPWUtils import Logger
from Hosts import Hosts
import time
import logging
import os.path

class Reader(Thread.Thread):
    ''' Wait for a datagram, then decode and forward to consumers '''
    def __init__(self, args:ArgumentParser) -> None:
        Thread.Thread.__init__(self, "Reader", args)
        self.__hosts = Hosts(args)
        self.__queues = []

    @staticmethod
    def addArgs(parser:ArgumentParser) -> None:
        Hosts.addArgs(parser)
        grp = parser.add_argument_group(description="UDP Listener options")
        grp.add_argument('--port', type=int, default=11113, metavar='port',
                help='Port to listen on')
        grp.add_argument("--size", type=int, default=16, help="Datagram size, power of 2 near 9")
        grp = grp.add_mutually_exclusive_group()
        grp.add_argument("--tcp", action="store_true", help="Connect using TCP")
        grp.add_argument("--udp", action="store_true", help="Connect using UDP datagrams")

    def addQueue(self, q:queue.Queue) -> None:
        self.__queues.append(q)

    def runIt(self) -> None:
        '''Called on thread start '''
        args = self.args
        qTCP = args.tcp
        packetSize = args.size
        hosts = self.__hosts
        queues = self.__queues
        logging.info("Starting TCP %s port %s size %s", qTCP, args.port, packetSize)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM if qTCP else socket.SOCK_DGRAM) as s:
            s.bind(('', args.port))

            if qTCP:
                s.listen() # Listen for incoming TCP connections
                logging.debug("TCP listening to port %s", args.port)

            while True: # Read TCP packets or UDP datagrams
                if qTCP: # Listen for a connection via TCP
                    (conn, senderAddr) = s.accept() # Got a connection request
                    with conn: # Close the connection cleanly when we leave with block
                        data = conn.recv(packetSize)
                else: # UDP get a datagram
                    (data, senderAddr) = s.recvfrom(packetSize)
                t = time.time()
                if not hosts.checkSignature(data[:2]):
                    logging.warning("Bad datagram received, %s, from %s", data, senderAddr)
                    continue
                logging.info("Received from %s n %s", senderAddr, data)
                host = hosts.hostFromNumber(data[-1:])
                if host is None:
                    logging.warning("Unrecognized host in, %s, from %s", data, senderAddr)
                    continue
                temp = host.decodeTemperature(data[2:4])
                free = host.decodeSpace(data[4:6])
                avail = host.decodeFraction(data[6:8])
                host = host.host()
                (ipAddr, port) = senderAddr
                body = (t, ipAddr, port, host, temp, free, avail)
                for q in queues: q.put(body)

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
Writer.addArgs(parser)
CSV.addArgs(parser)
args = parser.parse_args()

Logger.mkLogger(args)
logging.info("args=%s", args)

try:
    reader = Reader(args) # Create the UDP datagram reader thread
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
