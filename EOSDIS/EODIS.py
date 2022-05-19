#! /usr/bin/env python3
#
# Access NASA's EOSDIS, Earth Observing System Data Information System
#
# The developer portal with various APIs is at:
#  https://earthdata.nasa.gov/collaborate/open-data-services-and-software/api
#
# The CMR API:
#  https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html
#
# May-2022, Pat Welch, pat@mousebrains.com

from TPWUtils import Logger
from argparse import ArgumentParser
from PruneData import pruneData
from LoadYAML import loadYAML
from Credentials import loadCredentials
from SessionWithHeaderRedirection import Session
import requests
from Collections import collections,granules,duplicateURL
from Fetcher import fetchRaw
import json
import logging
import os
import sys

parser = ArgumentParser()
Logger.addArgs(parser)
parser.add_argument("--yaml", type=str, default="SUNRISE.yaml", help="YAML configuration file")
parser.add_argument("--credentials", type=str, default="~/.config/NASA/.credentials",
        help="Credentials for accessing NASA's EOSDIS information")
parser.add_argument("--raw", type=str, default="data/Raw", help="Where to store unpruned data")
parser.add_argument("--pruned", type=str, default="data/Pruned", help="Where to store pruned data")
grp = parser.add_argument_group(description="URL prefixes")
args = parser.parse_args()

logger = Logger.mkLogger(args, fmt="%(asctime)s %(levelname)s: %(message)s", logLevel=logging.INFO)

info = loadYAML(args.yaml)
logger.info("%s ->\n%s", args.yaml, json.dumps(info, indent=True, sort_keys=True))

for name in [args.raw, args.pruned]:
    if not os.path.isdir(name):
        logger.info("Making %s", name)
        os.makedirs(name, mode=0o755, exist_ok=True)
        
(username, codigo) = loadCredentials(args.credentials)
logging.info("Username %s codigo %s", username, codigo)

with requests.Session() as s: # For CMR and Granules, no authorizaton needed
    items = collections(s, info)
    if not items: 
        logger.warning("No CMR items found")
        sys.exit(1)
    logger.info("Fetched %s CMR items", len(items))
    urls = granules(s, info, items)
    if not urls: 
        logger.warning("No URLs found to fetch")
        sys.exit(1)
    if "regDup" in info: # Duplicate some entries with substitution, VIIRS Ocean Color case
        urls.update(duplicateURL(urls, info["regDup"]))

logger.info("Found %s URLs to fetch", len(urls))

with Session(username, codigo) as s: # For data fetching
    for url in urls:
        ofn = fetchRaw(s, url, urls[url], args.raw)
        if ofn: pruneData(info, ofn, args.pruned)
