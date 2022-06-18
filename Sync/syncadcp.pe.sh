#! /usr/bin/sh
#
pattern=PE22_31_Shearman_ADCP
platform=PE

log=/home/pat/logs/syncADCP.log

cmd="/usr/bin/rsync \
	--archive \
       	--verbose \
       	--exclude=adcpdb \
       	--exclude=config \
       	--exclude=cal \
       	--exclude=edit \
       	--exclude=grid \
       	--exclude=load \
       	--exclude=nav \
       	--exclude=ping \
       	--exclude=png_archive \
       	--exclude=quality \
       	--exclude=scan \
	--exclude=stick \
	--exclude=vector"

date >>$log


lastsrc=

for src in `ls -trd /mnt/adcp/${pattern}*`; do
	lastsrc=$src
	tgt=/mnt/sci/data/Platform/$platform/ADCP_UHDAS/`basename $src`
	mkdir -p $tgt
	$cmd $src/proc/* $tgt 2>&1 >>$log
done

if [ "x$lastsrc" != "x" ] ; then
	src=$lastsrc
	tgt=/mnt/sci/data/Platform/$platform/ADCP_UHDAS
	mkdir -p $tgt
	$cmd $src/proc/* $tgt 2>&1 >>$log
fi
