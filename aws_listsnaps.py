#!/bin/python3
import boto3

ec2 = boto3.resource('ec2')

print('Getting list of instances:\n\n')
for instance in ec2.instances.all():
    for tag in instance.tags:
        if tag['Key'] == 'Name':
            instance_name = tag['Value']
    print('Snapshots for {0}:'.format(instance_name))
    instance_root = instance.block_device_mappings[0]['Ebs']['VolumeId']
    snapshots = ec2.snapshots.filter(Filters=[{'Name': 'volume-id', 'Values': [instance_root]}])
    snaps = []
    for snap in snapshots:
        snaps.append((snap.start_time, snap.volume_size, snap.id))
    for snap in sorted(snaps, key=lambda snaps: snaps[0]):
        print('  {id} : {date} - {size} GB'.format(id=snap[2], date=snap[0].isoformat(), size=snap[1]))
    print('\n  Number of snapshots: {0}\n\n'.format(len(snaps)))
