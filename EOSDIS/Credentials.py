#! /usr/bin/env python3
#
# Load Credentials if they exist, else prompt and generate them
#
# May-2022, Pat Welch, pat@mousebrains.com

import yaml
import json
import os
import logging

def loadCredentials(fn:str) -> tuple[str, str]:
    fn = os.path.abspath(os.path.expanduser(fn))
    if os.path.isfile(fn): # file does not exist, so create the credentials
        with open(fn, "r") as fp:
            info = yaml.safe_load(fp)
            if "username" in info and "codigo" in info:
                return (info["username"], info["codigo"])

    dirname = os.path.dirname(fn) 
    if not os.path.isdir(dirname):
        logging.info("Creating %s", dirname)
        os.makedirs(dirname, mode=0o755, exist_ok=True)
    username = input("Enter username for NASA EOSDIS login: ")
    codigo = input("Enter password for NASA EOSDIS login: ")
    logging.info("Saving credentils to %s", fn)
    with open(fn, "w") as fp:
        yaml.dump(dict(username=username, codigo=codigo), fp)

    return (username, codigo)

if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("credentials", type=str, nargs="+",
            help="Credentials for accessing NASA's EOSDIS information")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose messages")
    args = parser.parse_args()

    logging.basicConfig(format="%(asctime)s %(levelname)s: %(message)s",
            level=logging.DEBUG if args.verbose else logging.INFO)

    for fn in args.credentials:
        (username, codigo) = loadCredentials(fn)
        logging.info("Username %s codigo %s", username, codigo)
