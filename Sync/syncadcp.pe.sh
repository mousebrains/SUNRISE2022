#! /usr/bin/sh
#
pattern=PE22_31_Shearman_ADCP

log=/home/pat/logs/syncADCP.log

date >>$log

for src in /mnt/adcp/${pattern}*; do
	tgt=/mnt/sci/data/Platform/PE/ADCP_UHDAS/`basename $src`
	mkdir -p $tgt
	/usr/bin/rsync \
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
		--exclude=vector \
		$src/proc/* \
		$tgt \
		2>&1 >>$log
done
