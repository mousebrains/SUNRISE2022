# These are specific to the SUNRISE shore side server syncthing setup.
For general syncthing installation [instructions](https://www.linuxfordevices.com/tutorials/ubuntu/syncthing-install-and-setup)

# Shore side specific instructions
- Connect to http://localhost:8384 via a ssh tunnel `ssh -L8384:localhost:8384 sunrise.ceoas.oregonstate.edu` from your local host
  - Delete the **Default Folder**
  - Add a **Shore** folder Sync/Shore send only
  - Add a **Pelican** folder Sync/Pelican receive only
  - Add a **PointSur** folder Sync/PointSur receive only
