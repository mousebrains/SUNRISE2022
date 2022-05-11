* Set up for shore side system:

- Install Ubuntu 22.04
- Install fail2ban, `sudo apt install fail2ban`
- Configure the [firewall](Shore.firewall.md)
- Setup [Public-Facing SSH access](Shore.SSH.md)
- Install the weberver:
  - `sudo apt install nginx`

- Setup git defaults for dealing with submodule recurssion
  - `git config --global user.email "you@example.com"`
  - `git config --global user.name "Your Name"`
  - `git config --global submodule.recurse true`
  - `git config --global diff.submodule log`
  - `git config --global status.submodulesummary 1`
  - `git config --global push.recurseSubmodules on-demand`
- Clone this repository, `git --recurse-submodules clone git@github.com:mousebrains/SUNRISE2022.git`
- Install syncthing using [instructions](https://www.linuxfordevices.com/tutorials/ubuntu/syncthing-install-and-setup)
  - `echo "deb https://apt.syncthing.net/ syncthing stable" | sudo tee /etc/apt/sources.list.d/syncthing.list`
  - `curl -s https://syncthing.net/release-key.txt | sudo apt-key add -`
  - `sudo apt update`
  - `sudo apt install syncthing`
  - `sudo systemctl enable syncthing@pat.service`
  - `sudo systemctl start syncthing@pat.service`
  - Connect to http://localhost:8384 via a ssh tunnel `ssh -L8384:localhost:8384 sunrise.ceoas.oregonstate.edu` from your local host
    - Delete the **Default Folder**
    - Add a **Shore** folder Sync/Shore send only
    - Add a **Pelican** folder Sync/Pelican receive only
    - Add a **PointSur** folder Sync/PointSur receive only
