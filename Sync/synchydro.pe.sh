#! /usr/bin/sh
#
log=/home/pat/logs/syncHydro.log

exclude0='*PS*'
src0=/mnt/sci/data/Processed_NC/HydroCombo 
tgt0=/home/pat/Sync/Pelican

exclude1='*PE*'
src1=/home/pat/Sync/PointSur/HydroCombo
tgt1=/mnt/sci/data/Processed_NC/

mkdir -p $tgt0 $tgt1

date >>$log

/usr/bin/rsync \
	--temp-dir=/home/pat/cache \
	--archive \
       	--verbose \
	--exclude=$exclude0 \
	$src0 $tgt0 2>&1 >>$log

/usr/bin/rsync \
	--temp-dir=/mnt/sci/cache \
	--archive \
       	--verbose \
	--exclude=$exclude1 \
	$src1 $tgt1 2>&1 >>$log
