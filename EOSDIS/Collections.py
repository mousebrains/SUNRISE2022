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
import datetime
import time
import logging
import sys

def fetchPages(session:requests.Session, url:str, params:dict) -> list:
    payload = params.copy() # Make a local copy
    payload["page_size"] = 1000
    items = []
    for pageNumber in range(1,100): # Avoid infinite loops
        payload["page_num"] = pageNumber
        with session.get(url, params=payload) as r:
            if r.status_code != 200:
                logging.error("Error fetching %s\n%s", r.url, r.content)
                return items
            info = r.json()
            if ("items" not in info) or (not len(info["items"])): return items
            items.extend(info["items"])
    logging.warning("Too many pages in fetchPages for %s, %s", url, params)
    return items

def cmrBaseURL(info:dict) -> str:
    if "cmrBaseURL" in info: return info["cmrBaseURL"]
    url = "https://cmr.earthdata.nasa.gov/search"
    logging.warning(f"cmrBaseURL not in information, using {url}")
    return url

def collections(session:requests.Session, info:dict) -> list:
    params = {
            "has_granules": "true",
            "downloadable": "true",
            }
    for key in ["collection_data_type", "provider", "processing_level_id", "instrument"]:
        if key in info and info[key]:
            params[key] = info[key]

    url = cmrBaseURL(info) + "/collections.umm_json_v1_4"
    items = fetchPages(session, url, params)

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

def mkBoundingBox(info:dict) -> dict:
    for key in ["lonMin", "lonMax", "latMin", "latMax"]:
        if key not in info or not isinstance(info[key], float): return {}

    return {"bounding_box": "{},{},{},{}".format(
                min(info["lonMin"], info["lonMax"]),
                min(info["latMin"], info["latMax"]),
                max(info["lonMin"], info["lonMax"]),
                max(info["latMin"], info["latMax"]),
                )}

def mkTemporal(info:dict) -> dict:
    if "daysBack" not in info or info["daysBack"] <= 0: return {}
    now = datetime.datetime.utcnow() # Current UTC time
    tStart = now - datetime.timedelta(days=info["daysBack"])
    tStr = tStart.strftime("%Y-%m-%dT%H:%M:%SZ")
    return {"temporal[]": f"{tStr},"}

def mkRevisionDate(grain:dict) -> float:
    if "meta" not in grain or "revision-date" not in grain["meta"]: return time.time()
    matches = re.fullmatch(
            r"(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})[.](\d{3})Z",
            grain["meta"]["revision-date"])
    if not matches: return time.time()
    revDate = datetime.datetime(
            int(matches[1]), int(matches[2]), int(matches[3]),
            int(matches[4]), int(matches[5]), int(matches[6]),
            int(matches[7]) * 1000)
    return revDate.timestamp()

def granules(session:requests.Session, info:dict, items:list) -> dict:
    params = mkBoundingBox(info)
    params.update(mkTemporal(info))

    url = cmrBaseURL(info) + "/granules.umm_json_v1_4"

    urls = {}
    for item in  items:
        if "concept-id" not in item["meta"]:
            logging.warning("No concept-id in\n%s",
                    json.dumps(item["meta"], indent=4, sort_keys=True))
            continue
        params["collection_concept_id"] = item["meta"]["concept-id"]
        grains = fetchPages(session, url, params)
        for grain in grains:
            if "umm" not in grain: continue
            umm = grain["umm"]
            if "RelatedUrls" not in umm: continue
            revDate = mkRevisionDate(grain)
            for rurl in umm["RelatedUrls"]:
                if "URL" in rurl and "Type" in rurl and rurl["Type"] == "GET DATA":
                    urls[rurl["URL"]] = revDate
    return urls

def duplicateURL(urls:dict, regDup:list) -> dict:
    items = {}
    for item in regDup:
        exp = re.compile(item[0])
        suffix = item[1]
        for url in urls:
            matches = exp.fullmatch(url)
            if not matches: continue
            items[matches[1] + suffix] = urls[url]
    return items

if __name__ == "__main__":
    from argparse import ArgumentParser
    from LoadYAML import loadYAML
    from TPWUtils import Logger
    import json

    parser = ArgumentParser()
    Logger.addArgs(parser)
    parser.add_argument("--granules", action="store_true", help="Also fetch granules")
    parser.add_argument("--yaml", type=str, help="YAML configuration file")
    parser.add_argument("--credentials", type=str, default="~/.config/NASA/.credentials",
        help="Credentials for accessing NASA's EOSDIS information")
    args = parser.parse_args()

    Logger.mkLogger(args, fmt="%(asctime)s %(levelname)s: %(message)s", logLevel=logging.INFO)

    info = loadYAML(args.yaml) if args.yaml else {}
    logging.info("YAML %s ->\n%s", args.yaml, json.dumps(info, indent=True, sort_keys=True))

    with requests.Session() as s:
        items = collections(s, info)
        logging.info("Fetched %s Collections", len(items))
        if items and not args.granules:
            logging.info("Collections\n%s", json.dumps(items, indent=4, sort_keys=True))
        if items and args.granules:
            urls = granules(s, info, items)
            logging.info("Fetched %s Granules", len(urls))
            if urls and "regDup" in info:
                urls.update(duplicateURL(urls, info["regDup"]))
            logging.info("Granules\n%s", json.dumps(urls, indent=4, sort_keys=True))
