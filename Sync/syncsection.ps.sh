#! /usr/bin/sh
#
log=/home/pat/logs/syncSection.log

src0=/mnt/sci/code/section/PS_section_definition.csv
tgt0=/home/pat/Sync/PointSur/section

src1=/home/pat/Sync/Pelican/section/PE_section_definition.csv
tgt1=/mnt/sci/code/section

mkdir -p $tgt0

date >>$log

/usr/bin/rsync --archive --verbose $src0 $tgt0 2>&1 >>$log
/usr/bin/rsync --archive --verbose $src1 $tgt1 2>&1 >>$log
