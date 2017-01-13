#!/bin/python3

import boto3
import urllib.request
import datetime
import time
import os
import subprocess
import glob

###
# Variables that you may want to change
###

instance_size = 'm4.2xlarge'  # No error checking!  Don't typo!
root_drive_size = 25  # In gigglebytes
root_drive_type = 'gp2'
security_groups = ['sg-de09a2b7', 'sg-e851fa81']
autoscale_group_name = 'mypillow'

clear_dirs = [
    '/var/log',
    '/var/cache'
]

clear_globs = [

]

clear_files = [

]

# Clear all of the log files/temporary files we don't need to capture in the AMI


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
    Name='mypillow.com@{0}'.format(time_string),
    Description='A mypillow.com worker node, taken at {0}.'.format(time_string),
    NoReboot=True,
    BlockDeviceMappings=[
        {
            'DeviceName': '/dev/sda1',
            'Ebs': {
                'VolumeSize': root_drive_size,
                'VolumeType': root_drive_type,
                'DeleteOnTermination': True,
            },
        },
    ]
)

# Kick off logrotate to alert all services to the absence of their log files

subprocess.call(['logrotate', '/etc/logrotate.conf', '-f'])

print('Created AMI {0}'.format(ami_response['ImageId']))

as_client = boto3.client('autoscaling')

lg_name = 'mypillow-worker-{0}'.format(time_string)

print('Creating Launch Group {0}...'.format(lg_name))

lg_response = as_client.create_launch_configuration(
    LaunchConfigurationName=lg_name,
    ImageId=ami_response['ImageId'],
    InstanceType=instance_size,
    SecurityGroups=security_groups,
    InstanceMonitoring={'Enabled': True},
    IamInstanceProfile='arn:aws:iam::148312753654:instance-profile/CodeDeploySampleStack-qiu3bm54gvh2v1ymygb9-InstanceRoleInstanceProfile-SYV9F6UEYJY0'
)

# Boto3 didn't provide a waiter for this, so I'll have to make one

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
    AutoScalingGroupName=autoscale_group_name,
    LaunchConfigurationName=lg_name
)