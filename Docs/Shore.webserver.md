* Set up the shore side web server:

- `sudo apt install nginx`
- Copy [sunrise](../SystemFiles/sunrise) to /etc/nginx/sites-available, `sudo cp sunrise /etc/nginx/sites-available`
- Enable sunrise `sudo ln -s /etc/nginx/sites-available/sunrise /etc/nginx/sites-enabled`
- Remove default `sudo rm /etc/nginx/sites-enabled/default`
- Restart the webserver `sudo systemctl restart nginx`
