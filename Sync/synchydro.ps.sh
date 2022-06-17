#! /usr/bin/sh
#
log=/home/pat/logs/syncHydro.log

exclude0='*PE*'
src0=/mnt/sci/data/Processed_NC/HydroCombo 
tgt0=/home/pat/Sync/PointSur

exclude1='*PS*'
src1=/home/pat/Sync/PointSur/HydroCombo
tgt1=/mnt/sci/data/Processed_NC/

date >>$log

/usr/bin/rsync \
	--archive \
       	--verbose \
	--exclude=$exclude0 \
	$src0 $tgt0 2>&1 >>$log

/usr/bin/rsync \
	--archive \
       	--verbose \
	--exclude=$exclude1 \
	$src1 $tgt1 2>&1 >>$log
