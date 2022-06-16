#! /usr/bin/env python3
#
# Install the service(s)
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
        os.makedirs(dirname, mode=0o755, exist_ok=True) # exist_ok=True is for race conditions
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

timers = set()
services = set()
timerServices = set()

for item in args.services:
    if item[-8:] == ".service":
        services.add(item)
    elif item[-6:] == ".timer":
        timers.add(item)
    else:
        print("Unsupported file suffix in", item)

if not timers and not services:
    print("No services specified")

for item in timers: # Now split out services with timers
    a = item.replace(".timer", ".service")
    if a in services:
        timerServices.add(a)
        services.remove(a)

toStart = services.union(timers) # Services and timers that need started
onlyServices = services.union(timerServices)
todos = list(toStart.union(timerServices)) # All services and timers 
print("services", services)
print("timers", timers)
print("timerServices", timerServices)
print("todos", todos)
print("toStart", toStart)
print("onlyServices", onlyServices)

makeDirectory(args.logdir) # Make sure the log directory exists
root = args.serviceDirectory # Where service files are stored
q = False # Was a new copy of any service file installed?
for service in todos:
    qq = maybeCopy(service, args.serviceDirectory)
    q |= qq

if not q and not args.force:
    print("No services were different")
    sys.exit(0)

print(f"Stopping {todos}")
cmd = [args.systemctl, "--user", "stop"]
cmd.extend(todos)
subprocess.run(cmd, shell=False, check=False) # Don't exit on error if services don't exist

print("Forcing reload of daemon")
subprocess.run((args.systemctl, "--user", "daemon-reload"),
        shell=False, check=True)

print(f"Enabling {todos}")
cmd = [args.systemctl, "--user", "enable"]
cmd.extend(todos)
subprocess.run(cmd, shell=False, check=True)

if toStart:
    print(f"Starting {toStart}")
    cmd = [args.systemctl, "--user", "start"]
    cmd.extend(toStart)
    subprocess.run(cmd, shell=False, check=True)

print("Enable lingering")
subprocess.run((args.loginctl, "enable-linger"), shell=False, check=True)

if onlyServices:
    print(f"Status {onlyServices}")
    cmd = [args.systemctl, "--user", "--no-pager", "status"]
    cmd.extend(onlyServices)
    s = subprocess.run(cmd, shell=False, check=False)

if timers:
    print(f"Timers {timers}")
    cmd = [args.systemctl, "--user", "--no-pager", "list-timers"]
    cmd.extend(timers)
    s = subprocess.run(cmd, shell=False, check=False)
