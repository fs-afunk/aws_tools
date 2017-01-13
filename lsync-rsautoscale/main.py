#!/usr/bin/env python
# -*- coding: utf-8 -*-

# vim: tabstop=4 shiftwidth=4 softtabstop=4

import boto3
import argparse
import os
import sys
import jinja2


def generate_lsync_config(addresses):
    env = jinja2.Environment(autoescape=True,
                             loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')))

    template = env.get_template('lsyncd.conf')

    print(template.render(server_list=addresses, source_dir='/var/www', dest_dir='/var/www'))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--as-group', required=True,
                        help='The autoscale group config ID')
    parser.add_argument('--region', required=False, default='SYD',
                        help='The region to authenticate to')

    args = vars(parser.parse_args())

    elbv2_client = boto3.client('elbv2')

    # Using credentials file
    try:
        pyrax.set_credential_file(os.path.expanduser("~/.cloud_credentials"))
    except Exception as e:
        sys.stderr.write("Failed to authenticate: %s" % str(e))

    au = pyrax.connect_to_autoscale(region=args['region'])
    cs = pyrax.connect_to_cloudservers(region=args['region'])

    as_group = au.get(args['as_group'])

    snet_ips = []

    for s_id in as_group.get_state()['active']:
        try:
            server = cs.servers.get(s_id)
            snet_ips.append(server.networks['private'][0])
        except:
            pass

    generate_lsync_config(snet_ips)


if __name__ == '__main__':
    main()
