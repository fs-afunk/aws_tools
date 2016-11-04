#!/bin/python3

import boto3
import urllib.request
import datetime
import time

ec2 = boto3.resource('ec2')
ec2_client = boto3.client('ec2')

with urllib.request.urlopen('http://169.254.169.254/latest/meta-data/instance-id') as f:
    my_id = f.read().decode('utf-8')

time_string = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

ami_response = ec2_client.create_image(
    DryRun=False,
    InstanceId=my_id,
    Name='go.puma.com@{0}'.format(time_string),
    Description='A go.puma.com worker node, taken at {0}.'.format(time_string),
    NoReboot=True,
    BlockDeviceMappings=[
        {
            'DeviceName': '/dev/sda1',
            'Ebs': {
                'VolumeSize': 40,
                'VolumeType': 'gp2',
                'DeleteOnTermination': False,
            },
        },
    ]
)

print('Created AMI {0}'.format(ami_response['ImageId']))

as_client = boto3.client('autoscaling')

lg_name = 'go.puma.com lc {0}'.format(time_string)

print('Creating Launch Group {0}...'.format(lg_name))

lg_response = as_client.create_launch_configuration(
    LaunchConfigurationName=lg_name,
    ImageId=ami_response['ImageId'],
    InstanceType='c4.2xlarge',
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
    AutoScalingGroupName='go.puma.com-autoscale',
    LaunchConfigurationName=lg_name
)