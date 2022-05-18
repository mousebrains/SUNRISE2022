#! /usr/bin/env python3
#
# Access NASA's EOSDIS, Earth Observing System Data Information System
# Fetch a list of granule direct data URLs to fetch
#
# The developer portal with various APIs is at:
#  https://earthdata.nasa.gov/collaborate/open-data-services-and-software/api
#
# The CMR API:
#  https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html
#
# May-2022, Pat Welch, pat@mousebrains.com

import requests
import datetime
import logging
import re
import datetime
import json
from Collections import cmrBaseURL, fetchPages

def cmrGranules(session:requests.Session, info:dict, items:dict) -> list[str]:
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

    urlPrefix = cmrBaseURL(info) + "/granules.umm_json_v1_4?" + "&".join(params) + "&"

    urls = {}
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
            if "meta" not in row: continue
            if "umm" not in row: continue
            umm = row["umm"]
            if "RelatedUrls" not in umm: continue
            if "revision-date" in row["meta"]:
                revDate = row["meta"]["revision-date"]
                matches = re.fullmatch(
                        r"(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})[.](\d{3})Z",
                        revDate)
                if matches:
                    revDate = datetime.datetime(
                            int(matches[1]), int(matches[2]), int(matches[3]),
                            int(matches[4]), int(matches[5]), int(matches[6]),
                            int(matches[7]) * 1000)
                else:
                    revDate = datetime.datetime.utcnow()
            else:
                revDate = datetime.datetime.utcnow()
            for rurl in row["umm"]["RelatedUrls"]:
                if "URL" in rurl and "Type" in rurl and rurl["Type"] == "GET DATA":
                    urls[rurl["URL"]] = revDate

    return urls if urls else None

if __name__ == "__main__":
    from argparse import ArgumentParser
    from Collections import cmrInfo
    from LoadYAML import loadYAML
    from TPWUtils import Logger

    parser = ArgumentParser()
    Logger.addArgs(parser)
    parser.add_argument("--yaml", type=str, help="YAML configuration file")
    parser.add_argument("--credentials", type=str, default="~/.config/NASA/.credentials",
            help="Credentials for accessing NASA's EOSDIS information")
    args = parser.parse_args()

    Logger.mkLogger(args, fmt="%(asctime)s %(levelname)s: %(message)s", logLevel=logging.INFO)

    info = loadYAML(args.yaml) if args.yaml else {}
    logging.info("%s ->\n%s", args.yaml, json.dumps(info, indent=True, sort_keys=True))

    with requests.Session() as session:
        items = cmrInfo(session, info)
        if items:
            logging.info("Fetched %s CMR items", len(items))

        granules = cmrGranules(session, info, items)
        logging.info("Found %s granules", len(granules) if granules else None)
        if granules:
            for url in sorted(granules):
                logging.info("Granule %s %s", granules[url], url)
