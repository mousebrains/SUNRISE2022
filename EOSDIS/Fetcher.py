#! /usr/bin/env python3
#
# Given a requests.Session and a url, write the fetched binary contents to a file
# This is designed to handle NetCDF and h5 types of content
#
# May-2022, Pat Welch, pat@mousebrains.com

import requests
import os
import datetime
import logging
import sys

def fetchRaw(session:requests.Session, url:str, tModified:datetime.datetime, dirname:str) -> str:
    basename = os.path.basename(requests.utils.urlparse(url).path)
    ofn = os.path.abspath(os.path.expanduser(os.path.join(dirname, basename)))

    if os.path.isfile(ofn) and (os.path.getmtime(ofn) < tModified.timestamp()):
        logging.info("No need to fetch %s", ofn)
        return ofn

    with session.get(url) as r:
        if r.status_code != 200:
            logging.warning("Unable to fetch, %s, %s", r.status_code, url)
            return None
        n = int(r.headers["Content-Length"]) if "Content-Length" in r.headers else len(r.content)
        logging.info("Fetched %s MB for %s", round(n/1024/1024), basename)
        with open(ofn, "wb") as fp: fp.write(r.content)
    return ofn

if __name__ == "__main__":
    from argparse import ArgumentParser
    from TPWUtils import Logger
    from SessionWithHeaderRedirection import Session
    from Credentials import loadCredentials

    parser = ArgumentParser()
    Logger.addArgs(parser)
    parser.add_argument("--credentials", type=str, default="~/.config/NASA/.credentials",
        help="Credentials for accessing NASA's EOSDIS information")
    parser.add_argument("--output", type=str, default=".", help="Where to store output files")
    parser.add_argument("--time", type=str, 
            default=datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"),
            help="Revision time to pass into fetchData")
    parser.add_argument("url", type=str, nargs="+", help="URLs to fetch")
    args = parser.parse_args()

    Logger.mkLogger(args, fmt="%(asctime)s %(levelname)s: %(message)s", logLevel=logging.INFO)

    t0 = datetime.datetime.strptime(args.time, "%Y-%m-%dT%H:%M:%S")

    (username, codigo) = loadCredentials(args.credentials)

    with Session(username, codigo) as s:
        for url in args.url:
            ofn = fetchRaw(s, url, t0, args.output)
            logging.info("ofn %s", ofn)
