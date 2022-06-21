#! /usr/bin/sh
#
src=/mnt/adcp/current_cruise
tgt=/home/pat/Sync/Pelican/ADCP

log=/home/pat/logs/syncADCP2Shore.log

date >>$log
/usr/bin/rsync --temp-dir=/home/pat/cache --archive --verbose $src/proc/*/contour/*.nc $tgt 2>&1 >>$log
