#! /usr/bin/env python3
#
# Load a YAML file safely
#
# May-2022, Pat Welch, pat@mousebrains.com

import yaml
import json
import os
import logging

def loadYAML(fn:str) -> dict:
    if not os.path.isfile(fn):
        logging.error("File %s does not exist!", fn)
        return None
    with open(fn, "r") as fp: return yaml.safe_load(fp)

if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("yaml", type=str, nargs="+", help="YAML file to parse")
    args = parser.parse_args()

    for fn in args.yaml:
        info = loadYAML(fn)
        print("Filename", fn)
        print(json.dumps(info, indent=4, sort_keys=True))
