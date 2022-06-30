#! /usr/bin/sh -x
#
# Rebuild the netcdf ShipDas files
#
# June-2022, Pat Welch, pat@mousebrains.com


if [ `hostname` = "ps0" ] ; then
	host=ps
	platform=PS
elif [ `hostname` = "pe0" ] ; then
	host=pe
	platform=PE
else
	echo Unrecognized hostname `hostname`
	exit 1
fi

systemctl --user stop met2nc.$host.timer

echo "UPDATE met SET qnetcdf=false WHERE ship='$host';" | psql

rm -f /mnt/sci/data/Platform/$platform/ShipDas/met.nc 

systemctl --user start met2nc.$host.service
systemctl --user start met2nc.$host.timer
