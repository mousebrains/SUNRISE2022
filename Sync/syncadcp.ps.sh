#! /usr/bin/sh
#
pattern=PS22_23_MacKinnon
platform=PS
otro=PE

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

for src in `ls -trd /mnt/adcp/${pattern}*`; do
	tgt=/mnt/sci/data/Platform/$platform/ADCP_UHDAS/`basename $src`
	mkdir -p $tgt
	echo >>$log
	echo "Source $src" >>$log
	echo "Target $tgt" >>$log
	$cmd --temp-dir=/mnt/sci/cache $src/proc/* $tgt 2>&1 >>$log
done

src=/mnt/adcp/current_cruise
tgt=/mnt/sci/data/Platform/$platform/ADCP_UHDAS
mkdir -p $tgt
echo >>$log
echo "Source $src" >>$log
echo "Target $tgt" >>$log
$cmd --temp-dir=/mnt/sci/cache $src/proc/* $tgt 2>&1 >>$log

# Copy over the Processed_NC/ADCP_UHDAS/*Platform* to Sync

src=/mnt/sci/data/Processed_NC/ADCP_UHDAS
tgt=/home/pat/Sync/PointSur/Processed_NC/ADCP_UHDAS
mkdir -p $tgt
echo >>$log
echo "Source $src" >>$log
echo "Target $tgt" >>$log
$cmd --temp-dir=/home/pat/cache $src/*_${platform}_*.nc $tgt

# Copy over the SyncProcessed_NC/ADCP_UHDAS/*Platform* to sci

src=/home/pat/Sync/Pelican/Processed_NC/ADCP_UHDAS
tgt=/mnt/sci/data/Processed_NC/ADCP_UHDAS
mkdir -p $tgt
echo >>$log
echo "Source $src" >>$log
echo "Target $tgt" >>$log
$cmd --temp-dir=/mnt/sci/cache $src/*_${otro}_*.nc $tgt
