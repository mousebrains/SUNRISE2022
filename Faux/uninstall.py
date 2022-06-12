#! /usr/bin/env python3
#
# uninstall the Faux service
#
# Feb-2022, Pat Welch, pat@mousebrains.com

from argparse import ArgumentParser
import subprocess
import os
import sys

parser = ArgumentParser()
parser.add_argument("--services", type=str, required=True, action="append", help="Service files")
parser.add_argument("--serviceDirectory", type=str, default="~/.config/systemd/user",
        help="Where to copy service file to")
parser.add_argument("--systemctl", type=str, default="/usr/bin/systemctl",
        help="systemctl executable")
args = parser.parse_args()

root = os.path.abspath(os.path.expanduser(args.serviceDirectory))

print(f"Stopping {args.services}")
cmd = [args.systemctl, "--user", "stop"]
cmd.extend(args.services)
subprocess.run(cmd, shell=False, check=True)

print(f"Disabling {args.services}")
cmd = [args.systemctl, "--user", "disable"]
cmd.extend(args.services)
subprocess.run(cmd, shell=False, check=True)

subprocess.run((args.systemctl, "--user", "daemon-reload"),
        shell=False, check=True)

for service in args.service:
    fn = os.path.join(fn, service)
    if os.path.isfile(fn):
        print(f"Removing {fn}")
        os.unlink(fn)
