#! /usr/bin/env python3
#
# Install the SSHtunnel service
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

def maybeCopy(src:str, tgt:str) -> bool:
    src = os.path.abspath(os.path.expanduser(src))
    tgt = makeDirectory(tgt)
    tgt = os.path.join(tgt, os.path.basename(src))

    if os.path.isfile(tgt):
        sContent = stripComments(src)
        tContent = stripComments(tgt)
        if sContent == tContent: return False

    with open(src, "r") as fp: content = fp.read()
    with open(tgt, "w") as fp: fp.write(content)
    return True

parser = ArgumentParser()
parser.add_argument("--force", action="store_true", help="Force reloading ...")
parser.add_argument("--serviceDirectory", type=str, default="~/.config/systemd/user",
        help="Where to copy service file to")
parser.add_argument("--systemctl", type=str, default="/usr/bin/systemctl",
        help="systemctl executable")
parser.add_argument("--loginctl", type=str, default="/usr/bin/loginctl",
        help="loginctl executable")
parser.add_argument("--logdir", type=str, default="~/logs", help="Where logfiles are stored")
parser.add_argument("services", type=str, nargs="+", help="Service file(s)")
args = parser.parse_args()

if args.services is None: args.services = ["pe.service", "ps.service"]

makeDirectory(args.logdir)

root = args.serviceDirectory
q = True
for service in args.services:
    qq = maybeCopy(service, args.serviceDirectory)
    q &= qq

if not q and not args.force:
    print("Nothing to be done")
    sys.exit(0)

print(f"Stopping {args.services}")
cmd = [args.systemctl, "--user", "stop"]
cmd.extend(args.services)
subprocess.run(cmd, shell=False, check=False)

print("Forcing reload of daemon")
subprocess.run((args.systemctl, "--user", "daemon-reload"),
        shell=False, check=True)

print(f"Enabling {args.services}")
cmd = [args.systemctl, "--user", "enable"]
cmd.extend(args.services)
subprocess.run(cmd, shell=False, check=True)

print(f"Starting {args.services}")
cmd = [args.systemctl, "--user", "start"]
cmd.extend(args.services)
subprocess.run(cmd, shell=False, check=True)

print("Enable lingering")
subprocess.run((args.loginctl, "enable-linger"), shell=False, check=True)

print(f"Status {args.services}")
cmd = [args.systemctl, "--user", "--no-pager", "status"]
cmd.extend(args.services)
s = subprocess.run(cmd, shell=False, check=False)
