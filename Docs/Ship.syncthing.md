# These are specific to the SUNRISE ship side server syncthing setup.
For general [instructions](syncthing.md)

# Pelican instructions
- Connect to http://localhost:8384 via a ssh tunnel `ssh -L8384:localhost:8384 localhostname`
  - Delete the **Default Folder**
  - Add a **Shore** folder Sync/Shore receive only
  - Add a **Pelican** folder Sync/Pelican send only
  - Add a **PointSur** folder Sync/PointSur receive only

# Point Sur instructions
- Connect to http://localhost:8384 via a ssh tunnel `ssh -L8384:localhost:8384 localhostname`
  - Delete the **Default Folder**
  - Add a **Shore** folder Sync/Shore receive only
  - Add a **Pelican** folder Sync/Pelican receive only
  - Add a **PointSur** folder Sync/PointSur send only
