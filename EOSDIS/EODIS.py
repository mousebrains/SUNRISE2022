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

from argparse import ArgumentParser
from PruneData import pruneData
from LoadYAML import loadYAML
from Credentials import loadCredentials
import xarray as xr
import requests
import yaml
import json
import datetime
import os
import sys
import re
import logging

def fetchPages(session:requests.sessions.Session, urlBase:str) -> list:
    items = []
    pageNumber = 0
    while True:
        pageNumber += 1
        url = urlBase + f"&page_num={pageNumber}"
        with session.get(url) as r:
            if r.status_code != 200 or len(r.content) == 0: break
            data = r.json()
            if "items" not in data or not data["items"]: break
            items.extend(data["items"])
    logging.debug("Fetched %s page(s) with %s items for %s",
            pageNumber - 1, len(items), urlBase)
    return items if items else None

def cmrInfo(session:requests.sessions.Session, info:dict, urlBase:str) -> list:
    urlBase += "/collections.umm_json_v1_4"
    params = ["page_size=1000"]
    params.append("has_granules=true")
    params.append("downloadable=true")
    for key in ["collection_data_type", "provider", "processing_level_id", "instrument"]:
        if key in info and info[key]:
            if isinstance(info[key], list):
                for item in info[key]:
                    params.append(f"{key}[]={item}")
            else:
                params.append(f"{key}={info[key]}")

    url = urlBase + "?" + "&".join(params)
    items = fetchPages(session, url)

    if "regexp" not in info or not items: return items

    # I couldn't figure out how to get CMR to filter Science Keywords for me, so do it here
    exp = re.compile(info["regexp"])
    keep = []
    skipped = set()
    for item in items:
        if "umm" not in item or "ScienceKeywords" not in item["umm"]:
            logging.info("No umm found in\n%s", json.dumps(item, indent=4, sort_keys=True))
            keep.append(item)
            continue
        for blk in item["umm"]["ScienceKeywords"]:
            if "VariableLevel1" in blk:
                val = blk["VariableLevel1"]
                if exp.search(val):
                    keep.append(item)
                    break
                skipped.add(val)
    if skipped: logging.info("Skipped %s", sorted(skipped))
    return keep


def cmrGranuales(session:requests.sessions.Session, info:dict, items:dict, urlBase:str) -> list[str]:
    # Using items fetched via cmrInfo, get URLs of granuales to fetch

    params = ["page_size=1000", "sort_key=start_date"]
    if "lonMin" in info and info["lonMin"] is not None and \
            "lonMax" in info and info["lonMax"] is not None and \
            "latMin" in info and info["latMin"] is not None and \
            "latMax" in info and info["latMax"] is not None:
        lonMin = min(info["lonMin"], info["lonMax"])
        lonMax = max(info["lonMax"], info["lonMax"])
        latMin = min(info["latMin"], info["latMax"])
        latMax = max(info["latMax"], info["latMax"])
        params.append(f"bounding_box[]={lonMin},{latMin},{lonMax},{latMax}")

    if "daysBack" in info and info["daysBack"] > 0:
        now = datetime.datetime.utcnow() # Current UTC time
        tStart = now - datetime.timedelta(days=info["daysBack"])
        tStr = tStart.strftime("%Y-%m-%dT%H:%M:%SZ")
        params.append(f"temporal[]={tStr},")

    urlPrefix = urlBase + "/granules.umm_json_v1_4?" + "&".join(params) + "&"

    urls = set()
    for item in items: # Now find granuales with data in our region and time of interest
        if "meta" not in item:
            logging.warning("No meta in\n%s", json.dumps(item, indent=4, sort_keys=True))
            continue
        if "concept-id" not in item["meta"]:
            logging.warning("No concept-id in meta\n%s", 
                    json.dumps(item["meta"], indent=4, sort_keys=True))
            continue
        conceptID = item["meta"]["concept-id"]

        # additional parameters
        url = urlPrefix + f"&collection_concept_id={conceptID}"

        a = fetchPages(session, url)
        if not a: continue
        for row in a: # Walk through granule rows
            if "umm" not in row: continue
            umm = row["umm"]
            if "RelatedUrls" not in umm: continue
            for rurl in row["umm"]["RelatedUrls"]:
                if "URL" in rurl and "Type" in rurl and rurl["Type"] == "GET DATA":
                    urls.add(rurl["URL"])

    return urls if urls else None

def fetchRaw(session:requests.sessions.Session, url:str, dirname:str) -> str:
    basename = os.path.basename(url)
    ofn = os.path.join(dirname, basename)
    if os.path.isfile(ofn): 
        logging.info("Exists %s", ofn)
        return ofn

    with session.get(url) as r:
        if r.status_code != 200: return None
        logging.info("Fetched %s MB for %s", round(len(r.content)/1024/1024), basename)
        with open(ofn, "wb") as fp: fp.write(r.content)
    return ofn

parser = ArgumentParser()
parser.add_argument("--yaml", type=str, default="SUNRISE.yaml", help="YAML configuration file")
parser.add_argument("--credentials", type=str, default="~/.config/NASA/.credentials",
        help="Credentials for accessing NASA's EOSDIS information")
parser.add_argument("--raw", type=str, default="data/Raw", help="Where to store unpruned data")
parser.add_argument("--pruned", type=str, default="data/Pruned", help="Where to store pruned data")
parser.add_argument("--verbose", action="store_true", help="Enable verbose messages")
grp = parser.add_argument_group(description="URL prefixes")
grp.add_argument("--cmr", type=str,
        default="https://cmr.earthdata.nasa.gov/search",
        help="Common Metadata Repository base URL for searches")
args = parser.parse_args()

logging.basicConfig(format="%(asctime)s %(levelname)s: %(message)s",
        level=logging.DEBUG if args.verbose else logging.INFO)

(username, codigo) = loadCredentials(args.credentials)
info = loadYAML(args.yaml)
logging.info("%s ->\n%s", args.yaml, json.dumps(info, indent=True, sort_keys=True))

for name in [args.raw, args.pruned]:
    if not os.path.isdir(name):
        logging.info("Making %s", name)
        os.makedirs(name, mode=0o755, exist_ok=True)
        
with requests.session() as session:
    items = cmrInfo(session, info, args.cmr)
    if not items: sys.exit(1)
    logging.info("Fetched %s CMR items", len(items))
    urls = cmrGranuales(session, info, items, args.cmr)
    if not urls: sys.exit(1)
    logging.info("Found %s URLs to fetch", len(urls))
    for url in urls:
        ofn = fetchRaw(session, url, args.raw)
        # if ofn: pruneData(info, ofn, args.pruned)
        # sys.exit(1)
