#! /usr/bin/env python3
#
# Run rsync on a set of input directories to a target directory
#
# June-2022, Pat Welch, pat@mousebrains.com

from argparse import ArgumentParser
import subprocess
from TPWUtils import Logger
import logging

parser = ArgumentParser()
Logger.addArgs(parser)
grp = parser.add_argument_group(description="Command options")
grp.add_argument("--rsync", type=str, default="/usr/bin/rsync")
grp.add_argument("--shell", action="store_true", help="Use a shell")
grp.add_argument("--opt", type=str, action="append", help="rsync options")
parser.add_argument("--tgt", type=str, required=True, help="Target of rsync command")
parser.add_argument("src", type=str, nargs="+", help="Source directories")
args = parser.parse_args()

Logger.mkLogger(args, fmt="%(asctime)s %(levelname)s: %(message)s")

if args.opt is None:
    args.opt = ["--archive", "--verbose", "--temp-dir", "/home/pat/cache"]

cmd = [args.rsync]
cmd.extend(args.opt)
cmd.extend(args.src)
cmd.append(args.tgt)

logging.info("%s", " ".join(cmd))

try:
    a = subprocess.run(cmd,
            shell=args.shell,
            capture_output=True,
            )
    if a.returncode:
        logging.error("Error, %s, executing %s", a.returncode, cmd)
    if a.stderr:
        try:
            logging.error("%s", str(a.stderr, "UTF-8"))
        except:
            logging.error("%s", a.stderr)
    if a.stdout:
        try:
            logging.info("%s", str(a.stdout, "UTF-8"))
        except:
            logging.info("%s", a.stdout)
except:
    logging.exception("Error executing %s", cmd)

