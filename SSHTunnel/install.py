#! /usr/bin/env python3
#
# Install a service for the SSH tunnel from this machine to shore
# so somebody on shore can log into the shipboard machine.
#
# Feb-2022, Pat Welch, pat@mousebrains.com

from argparse import ArgumentParser
import subprocess
from tempfile import NamedTemporaryFile
import os
import sys

def barebones(content:str) -> list[str]:
    lines = []
    for line in content.split("\n"):
        line = line.strip()
        if (len(line) == 0) or (line[0] == "#"): continue
        lines.append(line)
    return lines

parser = ArgumentParser()
parser.add_argument("--service", type=str, default="SSHtunnel", help="Service name")
parser.add_argument("--serviceDirectory", type=str, default="/etc/systemd/system",
        help="Where to copy service file to")
parser.add_argument("--force", action="store_true", help="Force writing a new file")
parser.add_argument("--systemctl", type=str, default="/usr/bin/systemctl",
        help="systemctl executable")
parser.add_argument("--cp", type=str, default="/usr/bin/cp", help="cp executable")
parser.add_argument("--chmod", type=str, default="/usr/bin/chmod", help="chmod executable")
parser.add_argument("--sudo", type=str, default="/usr/bin/sudo", help="sudo executable")
parser.add_argument("--logdir", type=str, default="~/logs", help="Where logfiles are stored")
args = parser.parse_args()

args.logdir = os.path.abspath(os.path.expanduser(args.logdir))
if not os.path.isdir(args.logdir):
    print("Creating", args.logdir)
    os.makedirs(args.logdir, mode=0o755, exist_ok=True)

ifn = os.path.abspath(os.path.expanduser(args.service + ".service"))
if not os.path.isfile(ifn):
    print(ifn, "does not exist")
    sys.exit(1)

with open(ifn, "r") as fp: input = fp.read() # Load the entire service file

ofn = os.path.join(args.serviceDirectory, f"{args.service}.service")

if not args.force and os.path.isfile(ofn):
    try:
        with open (ofn, "r") as fp:
            current = barebones(fp.read()) # Current contents
            proposed = barebones(input) # What we want to write
            if current == proposed:
                print("No need to update, identical")
                sys.exit(0)
    except:
        pass

# Write to a temporary file, then copy as root via sudo
with NamedTemporaryFile(mode="w") as fp:
    fp.write(input)
    fp.flush()
    print("Writing to", ofn)
    subprocess.run((args.sudo, args.cp, fp.name, ofn), shell=False, check=True)
    subprocess.run((args.sudo, args.chmod, "0644", ofn))

print("Forcing reload of daemon")
subprocess.run((args.sudo, args.systemctl, "daemon-reload"), shell=False, check=True)

print(f"Enabling {args.service}")
subprocess.run((args.sudo, args.systemctl, "enable", args.service), shell=False, check=True)

print(f"Starting {args.service}")
subprocess.run((args.sudo, args.systemctl, "restart", args.service), shell=False, check=True)

print(f"Status {args.service}")
s = subprocess.run((args.sudo, args.systemctl, "--no-pager", "status", args.service),
        shell=False, check=True)
