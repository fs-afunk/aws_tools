import boto3
import urllib.request
import os
import subprocess
import time

ec2 = boto3.resource('ec2')

print('Getting list of instances:')
for instance in ec2.instances.all():
    print(instance.id, end=' - ')
    for tag in instance.tags:
        if tag['Key'] == 'Name':
            print(tag['Value'])
instance_id = input('Which instance do you want?')
instance = ec2.Instance(instance_id)

root_volume = instance.block_device_mappings[0]['Ebs']['VolumeId']

print('Looks like the root volume for that machine is {0}.\nGetting snapshots for {0}...'.format(root_volume))
snapshots = ec2.snapshots.filter(Filters=[{'Name': 'volume-id', 'Values': [root_volume]}])

snaps = []
for snap in snapshots:
    snaps.append((snap.start_time, snap.volume_size, snap.id))

for snap in sorted(snaps, key=lambda snaps: snaps[0]):
    print('{id} : {date} - {size} GB'.format(id=snap[2], date=snap[0].isoformat(), size=snap[1]))

snap_id = input('Which snapshot do you want?')

client = boto3.client('ec2')

print('Cool.  Creating a volume from snapshot {}.'.format(snap_id))

nu_volume = client.create_volume(SnapshotId=snap_id, AvailabilityZone=instance.placement['AvailabilityZone'])
nu_volume_object = ec2.Volume(nu_volume['VolumeId'])

with urllib.request.urlopen('http://169.254.169.254/latest/meta-data/instance-id') as f:
    my_id = f.read().decode('utf-8')

print('Created volume {vol}.  Attaching to myself (known by few as {my_id}).'.format(vol=nu_volume_object.id, my_id=my_id))
print('Waiting for volume to be ready...')

while nu_volume_object.state != 'available':
    nu_volume_object.reload()
    time.sleep(1)

nu_volume_object.attach_to_instance(InstanceId=my_id, Device='/dev/sdf')

print('Waiting for kernel to notice the disk...')

while not os.path.exists('/dev/xvdf'):
    time.sleep(1)

proc = subprocess.call(['mount', '/dev/xvdf1', '/mnt/tmp'])
if proc is 0:
    print('Mounted the volume at /mnt/tmp on this system.  Open another shell, and do what you gotta do.')
    print("I'll sit here and wait.  Take your time.  Unmount with 'umount /mnt/tmp' when you're done.")

while os.path.ismount('/mnt/tmp'):
    time.sleep(1)

print('Alright, cleaning up.  Detaching volume...')
nu_volume_object.detach_from_instance()

while nu_volume_object.state != 'available':
    nu_volume_object.reload()
    time.sleep(1)

print('Volume detached.  Dropping it like a bad habit...')
client.delete_volume(VolumeId=nu_volume_object.id)
