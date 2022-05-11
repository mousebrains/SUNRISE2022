* Instructions for setting up a public-facing SSH server at Oregon State University

[Instructions](https://oregonstate.teamdynamix.com/TDClient/1935/Portal/KB/ArticleDet?ID=122712)

- Copy [osu_security.confg](../SystemFiles/osu_security.conf) to */etc/ssh/sshd_conf.d* `sudo cp osu_security.conf /etc/ssh/sshd_conf.d`
- Copy [banner.txt](../SystemFiles/banner.txt) to */etc/ssh* `sudo cp banner.txt /etc/ssh`
- Copy [motd](../SystemFiles/motd) to */etc/motd* `sudo cp motd /etc`

**SPLUNK** instructions from Tom
Using the Splunk Universal Forwarder is the standard method to aggregate SSH logs to the University’s central log server. Each IT support group is responsible for assisting their users with installing this forwarder and configuring it correctly. Once the forwarder is correctly configured, IS Infrastructure must allow the connection through the firewall via ticket request. This request is submitted to IS Infrastructure automatically in conjunction with the registration form mentioned above if the option “Is the Splunk Forwarder Installed” is “Yes”. Otherwise, the server owner/you must update the registration ticket once the forwarder is installed – OIS will then submit the request to IS Infrastructure on your behalf.

The latest version of the forwarder is available to IT Pros through our software server. Navigate to the path below to download the correct version for your system:

\\software.oregonstate.edu\software\Splunk\current

To Install:

Install the splunkforwarder package on your server.  The install will create a user named “splunk” using an unused UID and GID.  If a splunk user already exists in your directory, the installer will use that UID/GID instead.

- For example, on RHEL/CentOS use:

rpm -i splunkforwarder-8.0.6-152fb4b2bb96-linux-2.6-x86_64.rpm

- For Debian/Ubuntu use:

dpkg -i splunkforwarder-8.0.6-152fb4b2bb96-linux-2.6-amd64.deb

- Change to the splunk user to generate the input and output configurations.  A server.conf configuration file will be created the first time the splunkforwarder is executed.

su splunk

- Edit/create the file: /opt/splunkforwarder/etc/system/local/outputs.conf
<pre>
[tcpout]
defaultGroup = default-autolb-group
[tcpout:default-autolb-group]
server = splunk-prod-hf-vip.sig.oregonstate.edu:9997
[tcpout-server://splunk-prod-hf-vip.sig.oregonstate.edu:9997]
- Edit/create the file: /opt/splunkforwarder/etc/system/local/inputs.conf

[monitor:///var/log/secure*]
# [monitor:///var/log/auth.log*]
# ...Add other logs as necessary...
disabled=false
followSymlink=false
ignoreOlderThan=2d
#followTail=1
index=auth
</pre>
- As root, configure splunkforwarder to start up on a system boot.

sudo /opt/splunkforwarder/bin/splunk enable boot-start -systemd-managed 1 -user splunk

This appears to be your first time running this version of Splunk.
Splunk software must create an administrator account during startup. Otherwise, you cannot log in.
Create credentials for the administrator account.
Characters do not appear on the screen when you type in credentials.
Please enter an administrator username: <select an admin account>
Please enter a new password: <select an admin password>
Systemd unit file installed at /etc/systemd/system/SplunkForwarder.service.
Configured as systemd managed service.
 

- To start the splunk forwarder:  systemctl start SplunkForwarder

(or as the splunk user: /opt/splunkforwarder/bin/splunk start )

- To stop the splunk forwarder:  systemctl stop SplunkForwarder

(or as the splunk user: /opt/splunkforwarder/bin/splunk stop )

 

Once the forwarder is configured, have the server owner complete the SSH registration form and select “Yes” for “Is the Splunk forwarder installed.” This will prompt a ticket to be sent to IS Infrastructure requesting an exception for your server on the firewall.
</pre>
