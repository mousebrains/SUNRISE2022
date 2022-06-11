# PostgreSQL database schema

# To install use the script [../Setup/postgresql.setup](../Setup/postgresql.setup) which does the following:
 - `sudo apt install postgresql postgresql-client`
 - `sudo -u postgres createuser $LOGNAME`
 - `sudo -u postgres createdb --owner=$LOGNAME sunrise "SUNRISE 2022 database"`
 - `echo '\pset pager off' >~/.psqlrc`
 - `echo export PGDATABASE=sunrise >>~/.bashrc`
