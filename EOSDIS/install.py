#! /usr/bin/env python3
#
# Install a service for the EOSDIS fetcher
#
# Feb-2022, Pat Welch, pat@mousebrains.com

from argparse import ArgumentParser
import subprocess
from tempfile import NamedTemporaryFile
import os

parser = ArgumentParser()
parser.add_argument("--service", type=str, default="EOSDIS.service", help="Service file")
parser.add_argument("--timer", type=str, default="EOSDIS.timer", help="Timer file")
parser.add_argument("--serviceDirectory", type=str, default="/etc/systemd/system",
        help="Where to copy service and timer files to")
parser.add_argument("--systemctl", type=str, default="/usr/bin/systemctl",
        help="systemctl executable")
parser.add_argument("--cp", type=str, default="/usr/bin/cp",
        help="cp executable")
parser.add_argument("--sudo", type=str, default="/usr/bin/sudo",
        help="sudo executable")
parser.add_argument("--logdir", type=str, default="~/logs", help="Where logfiles are stored")
args = parser.parse_args()

args.logdir = os.path.abspath(os.path.expanduser(args.logdir))
if not os.path.isdir(args.logdir):
    print("Creating", args.logdir)
    os.makedirs(args.logdir, mode=0o755, exist_ok=True)

root = os.path.abspath(os.path.expanduser(args.serviceDirectory))

fn = os.path.join(root, os.path.basename(args.service))
print("Writing to", fn)
subprocess.run((args.sudo, args.cp, args.service, fn), shell=False, check=True)

fn = os.path.join(root, os.path.basename(args.timer))
print("Writing to", fn)
subprocess.run((args.sudo, args.cp, args.timer, fn), shell=False, check=True)

print("Forcing reload of daemon")
subprocess.run((args.sudo, args.systemctl, "daemon-reload"), shell=False, check=True)

print(f"Enabling {args.service}")
subprocess.run((args.sudo, args.systemctl, "enable", args.service), shell=False, check=True)

print(f"Enabling {args.timer}")
subprocess.run((args.sudo, args.systemctl, "enable", args.timer), shell=False, check=True)

print(f"Starting {args.timer}")
subprocess.run((args.sudo, args.systemctl, "start", args.timer), shell=False, check=True)

print(f"Status {args.service} and {args.timer}")
s = subprocess.run((args.sudo, args.systemctl, "--no-pager", "status", args.service, args.timer),
        shell=False, check=False)

print(f"List timer {args.timer}")
s = subprocess.run((args.sudo, args.systemctl, "--no-pager", "list-timers", args.timer),
        shell=False, check=True)
