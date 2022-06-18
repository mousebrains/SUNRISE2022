#! /usr/bin/sh
#
# I tried this using 
log=/home/pat/logs/syncADCP.log

date >>$log

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
	/mnt/adcp/current_cruise/proc/* \
	/mnt/sci/data/Platform/PS/ADCP_UHDAS \
	2>&1 >>$log
