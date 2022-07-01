#! /usr/bin/sh -x
#
# Rebuild the full database from the CSV files
# Then rebuild the CSV file going to the other ship
# Then rebuild the NetCDF files for local consumption
#
# June-2022, Pat Welch, pat@mousebrains.com


if [ `hostname` = "ps0" ] ; then
	host=ps
	platform=PS
	sync="PointSur"
	filepos="/mnt/data/PS22_23.%.csv"
elif [ `hostname` = "pe0" ] ; then
	host=pe
	platform=PE
	sync="Pelican"
	filepos="/mnt/data/MIDAS_%.elg"
else
	echo Unrecognized hostname `hostname`
	exit 1
fi

systemctl --user stop met.$host.service
systemctl --user stop met2csv.$host.timer
systemctl --user stop met2nc.$host.timer

echo "DELETE FROM met WHERE ship='$host';" | psql
echo "DELETE FROM fileposition WHERE filename like '$filepos';" | psql

systemctl --user start met.$host.service # Reload the database

rm -f ~/Sync/$sync/met.$host.csv
systemctl --user start met2csv.$host.service # Rebuild the CSV
systemctl --user start met2csv.$host.timer # Periodically rebuild it

rm -f /mnt/sci/data/Platform/$platform/ShipDas/met.nc 
systemctl --user start met2nc.$host.service
systemctl --user start met2nc.$host.timer
