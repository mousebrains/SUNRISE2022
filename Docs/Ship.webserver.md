# Set up the shore side web server:

- The following instructions are in [../Setup/web.setup](../Setup/web.setup)
- `sudo apt install nginx php-fpm`
- Change the user NGINX is running as, change all instances of *www-data* to pat in /etc/nginx/nginx.conf
- Change the user/group fpm-php is running as, change all instances of *www-data* to pat in /etc/php/8.1/fpm/pool.d/www.conf
- `sudo cp ~/SUNRISE2022/SystemFiles/sunrise.ship /etc/nginx/sites-available/sunrise`
- `sudo ln -sf /etc/nginx/sites-available/sunrise /etc/nginx/sites-enabled`
- `sudo rm /etc/nginx/sites-enabled/default`
- `sudo nginx -t` # Check the configuration
- `sudo systemctl restart nginx php8.1-fpm.service` # Restart the webserver and php-fpm
