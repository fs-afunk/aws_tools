#!/bin/python3

import boto3
import urllib.request
import datetime
import time
import os
import subprocess
import glob

# Clear all of the log files/temporary files we don't need to capture in the AMI

clear_dirs = [
    '/var/log',
    '/var/cache',
    '/var/www/vhosts/mannlakeltd.com/logs',
    '/var/www/vhosts/mannlakeltd.com/httpdocs/var/report',
    '/var/www/vhosts/mannlakeltd.com/httpdocs/var/log',
    '/var/www/vhosts/mannlakeltd.com/httpdocs/var/cache',
    '/var/www/vhosts/mannlakeltd.com/httpdocs/var/session'

]

clear_globs = [

]

clear_files = []

for pattern in clear_globs:
    clear_files.extend(glob.glob(pattern))

for clear_dir in clear_dirs:
    for root, dirs, files in os.walk(clear_dir):
        clear_files.extend(['{0}/{1}'.format(root, i) for i in files])

for file in clear_files:
    os.remove(file)

# Now that the files are clear, let's take a snapshot.

ec2 = boto3.resource('ec2')
ec2_client = boto3.client('ec2')

with urllib.request.urlopen('http://169.254.169.254/latest/meta-data/instance-id') as f:
    my_id = f.read().decode('utf-8')

time_string = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

ami_response = ec2_client.create_image(
    DryRun=False,
    InstanceId=my_id,
    Name='mannlakeltd.com@{0}'.format(time_string),
    Description='A mannlakeltd.com worker node, taken at {0}.'.format(time_string),
    NoReboot=True,
    BlockDeviceMappings=[
        {
            'DeviceName': '/dev/sda1',
            'Ebs': {
                'VolumeSize': 20,
                'VolumeType': 'gp2',
                'DeleteOnTermination': True,
            },
        },
    ]
)

# Kick off logrotate to alert all services to the absence of their log files

subprocess.call(['logrotate', '/etc/logrotate.conf', '-f'])

print('Created AMI {0}'.format(ami_response['ImageId']))

as_client = boto3.client('autoscaling')

lg_name = 'mannlakeltd.com lc {0}'.format(time_string)

print('Creating Launch Group {0}...'.format(lg_name))

lg_response = as_client.create_launch_configuration(
    LaunchConfigurationName=lg_name,
    ImageId=ami_response['ImageId'],
    InstanceType='c4.xlarge',
    SecurityGroups=['sg-01651266'],
    InstanceMonitoring={'Enabled': True}
)

# Boto3 didn't provide a watier for this, so I'll have to make one

timeout = time.time() + 30
while True:
    if len(as_client.describe_launch_configurations(LaunchConfigurationNames=[lg_name])['LaunchConfigurations']) > 0:
        break
    elif time.time() > timeout:
        print('Timed out waiting for Launch Configuration creation.')
        exit(1)
    time.sleep(1)

print('Launch group created.  Modifying AutoScale Group...')

asg_response = as_client.update_auto_scaling_group(
    AutoScalingGroupName='mannlakeltd.com',
    LaunchConfigurationName=lg_name
)