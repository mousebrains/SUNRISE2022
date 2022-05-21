# Set up the shore side web server:

- `sudo apt install nginx php-fpm`
- Change the user NGINX is running as, change all instances of *www-data* to pat in /etc/nginx/nginx.conf
- Change the user/group fpm-php is running as, change all instances of *www-data* to pat in /etc/php/8.1/fpm/pool.d/www.conf
- Copy [sunrise](../SystemFiles/sunrise) to /etc/nginx/sites-available, `sudo cp sunrise /etc/nginx/sites-available`
- Enable sunrise `sudo ln -s /etc/nginx/sites-available/sunrise /etc/nginx/sites-enabled`
- Remove default `sudo rm /etc/nginx/sites-enabled/default`
- Check the configuration `sudo nginx -t`
- Restart the webserver and php-fpm `sudo systemctl restart nginx php8.1-fpm.service`
