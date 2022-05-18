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

import requests
import re
import logging

def cmrBaseURL(info:dict) -> str:
    if "cmrBaseURL" not in info: 
        url = "https://cmr.earthdata.nasa.gov/search"
        info["cmrBaseURL"] = url
        logging.warning(f"cmrBaseURL not in information, using {url}")
    return info["cmrBaseURL"]

def fetchPages(session:requests.Session, urlBase:str) -> list:
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
    logging.debug("Fetched %s page(s) with %s items for %s", pageNumber - 1, len(items), urlBase)
    return items if items else None

def cmrInfo(session:requests.Session, info:dict) -> list:
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

    url = cmrBaseURL(info) + "/collections.umm_json_v1_4?" + "&".join(params)
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

if __name__ == "__main__":
    from argparse import ArgumentParser
    from LoadYAML import loadYAML
    from TPWUtils import Logger
    import json

    parser = ArgumentParser()
    Logger.addArgs(parser)
    parser.add_argument("--yaml", type=str, help="YAML configuration file")
    parser.add_argument("--credentials", type=str, default="~/.config/NASA/.credentials",
        help="Credentials for accessing NASA's EOSDIS information")
    args = parser.parse_args()

    Logger.mkLogger(args, fmt="%(asctime)s %(levelname)s: %(message)s", logLevel=logging.INFO)

    info = loadYAML(args.yaml) if args.yaml else {}
    logging.info("%s ->\n%s", args.yaml, json.dumps(info, indent=True, sort_keys=True))

    with requests.Session() as s:
        items = cmrInfo(s, info)
        if items:
            logging.info("Fetched %s CMR items", len(items))
            logging.info("Content:\n%s", json.dumps(items, indent=4, sort_keys=True))
