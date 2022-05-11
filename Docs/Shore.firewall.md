# Firewall setup
- `sudo ufw allow from 10.0.0.0/8 to 0.0.0.0/0 app OpenSSH comment "OSU private network"`
- `sudo ufw allow from 128.193.0.0/16 to 0.0.0.0/0 app OpenSSH comment "OSU public network"`
- `sudo ufw allow "Nginx Full"`
- `sudo ufw enable`
