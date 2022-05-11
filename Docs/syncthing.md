# Set up Ubuntu to use the latest syncthing

- Install syncthing using [instructions](https://www.linuxfordevices.com/tutorials/ubuntu/syncthing-install-and-setup)
  - `echo "deb https://apt.syncthing.net/ syncthing stable" | sudo tee /etc/apt/sources.list.d/syncthing.list`
  - `curl -s https://syncthing.net/release-key.txt | sudo apt-key add -`
  - `sudo apt update`
  - `sudo apt install syncthing`
  - `sudo systemctl enable syncthing@pat.service`
  - `sudo systemctl start syncthing@pat.service`

- [Shore side instructions](Shore.syncthing.md)
- [Ship side instructions](Ship.syncthing.md)
