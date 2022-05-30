#! /usr/bin/env python3
#
# Install a service for the EOSDIS fetcher
#
# Feb-2022, Pat Welch, pat@mousebrains.com

from argparse import ArgumentParser
import subprocess
import os
import sys

def makeDirectory(dirname:str) -> str:
    dirname = os.path.abspath(os.path.expanduser(dirname))
    if not os.path.isdir(dirname):
        print("Creating", dirname)
        os.makedirs(dirname, mode=0o755, exist_ok=True) # exist_ok=True os for race conditions
    return dirname

def stripComments(fn:str) -> str:
    lines = []
    with open(fn, "r") as fp:
        for line in fp.readlines():
            index = line.find("#")
            if index >= 0:
                line = line[:index]
            line = line.strip()
            if line: lines.append(line)
    return "\n".join(lines)

def maybeCopy(files:list[str], tgtDirectory:str) -> bool:
    qCopied = False
    tgtDirectory = makeDirectory(tgtDirectory)
    for src in files:
        src = os.path.abspath(os.path.expanduser(src))
        tgt = os.path.join(tgtDirectory, os.path.basename(src))

        if os.path.isfile(tgt):
            sContent = stripComments(src)
            tContent = stripComments(tgt)
            if sContent == tContent: continue

        with open(src, "r") as fp: content = fp.read()
        with open(tgt, "w") as fp: fp.write(content)
        qCopied = True
    return qCopied

parser = ArgumentParser()
parser.add_argument("--force", action="store_true", help="Force reloading ...")
parser.add_argument("--service", type=str, action="append", help="Service file(s)")
parser.add_argument("--timer", type=str, action="append", help="Timer file(s)")
parser.add_argument("--serviceDirectory", type=str, default="~/.config/systemd/user",
        help="Where to copy service and timer files to")
parser.add_argument("--systemctl", type=str, default="/usr/bin/systemctl",
        help="systemctl executable")
parser.add_argument("--loginctl", type=str, default="/usr/bin/loginctl",
        help="loginctl executable")

parser.add_argument("--logdir", type=str, default="~/logs", help="Where logfiles are stored")
args = parser.parse_args()

if args.service is None: args.service = ["EOSDIS.service", "SSS.service"]
if args.timer is None: args.timer = ["EOSDIS.timer", "SSS.timer"]

makeDirectory(args.logdir)

root = args.serviceDirectory
qService = maybeCopy(args.service, args.serviceDirectory)
qTimer   = maybeCopy(args.timer,   args.serviceDirectory)

if not qService and not qTimer and not args.force:
    print("Nothing to be done")
    sys.exit(0)

print("Forcing reload of daemon")
subprocess.run((args.systemctl, "--user", "daemon-reload"), shell=False, check=True)

print("Enabling", " ".join(args.service), " ".join(args.timer))
cmd = [args.systemctl, "--user", "enable"]
cmd.extend(args.service)
cmd.extend(args.timer)
subprocess.run(cmd, shell=False, check=True)

print("Starting", " ".join(args.timer))
cmd = [args.systemctl, "--user", "start"]
cmd.extend(args.timer)
subprocess.run(cmd, shell=False, check=True)

print("Enable lingering")
subprocess.run((args.loginctl, "enable-linger"), shell=False, check=True)

print("Status", " ".join(args.service), "and", " ".join(args.timer))
cmd = [args.systemctl, "--user", "--no-pager", "status"]
cmd.extend(args.service)
cmd.extend(args.timer)
subprocess.run(cmd, shell=False, check=True)

print(f"List timer {args.timer}")
cmd = [args.systemctl, "--user", "--no-pager", "list-timers"]
cmd.extend(args.timer)
subprocess.run(cmd, shell=False, check=True)
