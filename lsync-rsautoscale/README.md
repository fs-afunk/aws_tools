lsyncd-autoscale
================

Generate lsyncd config for autoscale group automatically

Currently lsync config files need to be generated on the master and need to contain all slave servers.
If slave servers come and go (such as in an autoscale environment) these need to be managed automatically in the lsyncd config file.

This project aims to read autoscale group members from API calls and generate an lsyncd configuration file from this information.

By default this script will have source and destination directories set to /var/www
modify main.py to change this

TODO: config files ;)

pyrax throws some warning output to stderr so to execute this script use the following command line
```
python main.py --as-group=AUTOSCALE_GROUP_ID 2>/dev/null > /etc/lsyncd.conf
```

This can be added to a cronjob
```
* * * * * root python /root/lsync-rsautoscale/main.py --as-group=<as-group> --region=HKG 2>/var/log/lsync-autoscale.error_log > /etc/lsyncd.conf; service lsyncd reload
```


Setup
=====

Go to the parent directory of where you want to install to. In this example, /opt/
```
cd /opt/
```

Download the zip file
```
sudo wget https://github.com/boxidau/lsync-rsautoscale/archive/master.zip -O lsync-rsautoscale.zip
```

Make sure you have the unzip system package
```
sudo apt-get install unzip
```

Unzip the utility and adjust the directory name
```
sudo unzip lsync-rsautoscale.zip
sudo mv lsync-rsautoscale-master lsync-rsautoscale
sudo rm lsync-rsautoscale.zip
```

Move into the directory
```
cd lsync-rsautoscale
```

Install required system packages. In Ubuntu 14.04, you will need:
```
sudo apt-get -y install python-dev python-pip

sudo  pip install -r requirements.txt
```

For Ubuntu, create the lsyncd log directory
```
sudo mkdir /var/log/lsyncd/
```

Create a file called .cloud_credentials in the home directory
```
[rackspace_cloud]
username = RACKSPACE_USERNAME
api_key = RACKSPACE_API_KEY
```

Create a cron job file. In this example, we will call it /etc/cron.d/lsync-rsautoscale
```
* * * * * root python /opt/lsync-rsautoscale/main.py --as-group=AUTOSCALE_GROUP_ID --region=REGION > /etc/lsyncd/lsyncd.conf.lua 2>/var/log/lsync-autoscale.error_log; service lsyncd reload
```

