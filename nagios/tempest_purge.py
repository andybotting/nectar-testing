#!/usr/bin/env python
from __future__ import print_function

import argparse
import os
import subprocess
import sys
import yaml

VIRTUALENV = '/opt/tempest'


def run(command):
    popen = subprocess.Popen(command, shell=True)
    popen.wait()
    return popen


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-e', '--environment', action='store',
                        required=True,
                        help='Set the environment')
    parser.add_argument('-s', '--site', action='store',
                        default=None,
                        help='site for configuration')
    parser.add_argument('--no-dry-run', action='store_true',
                        default=False,
                        help='site for configuration')

    args = parser.parse_args()

    if args.site:
        account = args.site
    else:
        account = args.environment

    environment = args.environment

    # Read ospurge needed variables
    base_path = os.path.dirname(os.path.realpath(__file__))

    with open(os.path.join(base_path,
              '../tempest/config/environments/' + environment + '.yaml')) as f:
        env_config = yaml.load(f)
    auth_url = env_config["config"]["identity"]["uri_v3"]

    with open(os.path.join(base_path,
              '../tempest/accounts/' + account + '.yaml')) as f:
        account_config = yaml.load(f)
    username = account_config[0]["username"]
    project = account_config[0]["project_name"]
    password = account_config[0]["password"]
    projdomain = account_config[0].get("project_domain_id", "default")
    userdomain = account_config[0].get("user_domain_id", "default")

    if args.no_dry_run:
        action = '--verbose'
    else:
        action = '--verbose --dry-run'

    cmd = ("ospurge {action} --purge-own-project "
           "--os-auth-url {auth_url} --os-username {username} "
           "--os-password {password} --os-user-domain-id {userdomain} "
           "--os-project-domain-id {projdomain} --os-project-name {project}"
           "".format(action=action, auth_url=auth_url, username=username,
                     password=password, userdomain=userdomain,
                     projdomain=projdomain, project=project))

    print("Running: {}".format(cmd.replace(password, 'xxxx')))
    popen = run(cmd)

    sys.exit(popen.returncode)


if __name__ == '__main__':
    main()
