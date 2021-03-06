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
from PruneSSS import pruneSSS
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
parser.add_argument("--force", action="store_true", help="Force downloading")
parser.add_argument("--yaml", type=str, default="SUNRISE.yaml", help="YAML configuration file")
parser.add_argument("--credentials", type=str, default="~/.config/NASA/.credentials",
        help="Credentials for accessing NASA's EOSDIS information")
parser.add_argument("--raw", type=str, default="data/Raw", help="Where to store unpruned data")
parser.add_argument("--pruned", type=str, default="data/Pruned", help="Where to store pruned data")
grp = parser.add_argument_group(description="URL prefixes")
args = parser.parse_args()

logger = Logger.mkLogger(args, fmt="%(asctime)s %(levelname)s: %(message)s", logLevel=logging.INFO)

try:
    info = loadYAML(args.yaml)
    logger.debug("%s ->\n%s", args.yaml, json.dumps(info, indent=True, sort_keys=True))

    for name in [args.raw, args.pruned]:
        if not os.path.isdir(name):
            logger.info("Making %s", name)
            os.makedirs(name, mode=0o755, exist_ok=True)
        
    (username, codigo) = loadCredentials(args.credentials)

    with requests.Session() as s: # For CMR and Granules, no authorizaton needed
        items = collections(s, info)
        if not items: 
            logger.info("No CMR items found")
            sys.exit(0)
        logger.info("Fetched %s CMR items", len(items))
        urls = granules(s, info, items)
        if not urls: 
            logger.info("No URLs found to fetch")
            sys.exit(0)
        if "regDup" in info: # Duplicate some entries with substitution, VIIRS Ocean Color case
            urls.update(duplicateURL(urls, info["regDup"]))

    logger.info("Found %s URLs to fetch", len(urls))

    with Session(username, codigo) as s: # For data fetching
        for url in urls:
            ofn = fetchRaw(s, url, urls[url], args.raw, args.force)
            if ofn: 
                if "pruner" in info: # Pruner specified
                    if info["pruner"] == "SSS": # Sea Surface Salinity pruner
                        pruneSSS(info, ofn, args.pruned)
                        continue
                pruneData(info, ofn, args.pruned) # Fell through to default for MODIS/VIIRS
except SystemExit:
    pass # Ignore sys.exit calls
except:
    logger.exception("Unexpected exception")
