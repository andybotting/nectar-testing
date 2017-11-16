#!/usr/bin/env python
from __future__ import print_function

import argparse
import os.path
import subprocess
import configparser
import yaml


def write_config(yaml_config, config_file, environment, site=None, host=None,
                 image=None, job=None):
    config = configparser.ConfigParser()
    config.read([config_file])

    y = yaml.load(yaml_config)
    for s in y.keys():
        if s != 'DEFAULT':
            try:
                config.add_section(s)
            except configparser.DuplicateSectionError:
                pass
        for entry in y[s]:
            config.set(s, entry, str(y[s][entry]))

    # force_host
    if site and host:
        nova_az = config.get('compute', 'availability_zone')
        nova_az = nova_az + ":" + host
        config.set('compute', 'availability_zone', nova_az)

    # set image ref
    if image:
        config.set('compute', 'image_ref', image)

    # Set path to accounts
    dir_path = os.path.dirname(os.path.realpath(__file__))

    if job and job.startswith("check"):
        accounts_file = os.path.join(dir_path,
                                     'accounts/tempest-operator.yaml')
    elif site:
        accounts_file = os.path.join(dir_path, 'accounts', '%s.yaml' % site)
    else:
        accounts_file = os.path.join(dir_path,
                                     'accounts', '%s.yaml' % environment)
    config.set('auth', 'test_accounts_file', accounts_file)

    # Write config
    with open(config_file, 'w') as f:
        config.write(f)


def execute(command, cwd=None):

    popen = subprocess.Popen(command, stdout=subprocess.PIPE, cwd=cwd)
    return popen.stdout.read().decode('utf-8')


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('workdir',
                        help='Tempest working dir.')
    parser.add_argument('-j', '--job', action='store',
                        default=None,
                        help='Job name for configuration')
    parser.add_argument('-e', '--environment', action='store',
                        default='production',
                        choices=['production', 'testing', 'development'],
                        help='Environment for configuration')
    parser.add_argument('-s', '--site', action='store',
                        default=None,
                        help='site for configuration')
    parser.add_argument('--host', action='store',
                        nargs='?', default=None,
                        help='Hypervisor to test')
    parser.add_argument('--image', action='store',
                        default=None,
                        help='Community image ID to test')
    args = parser.parse_args()

    hiera_command = ['hiera', '-f', 'yaml', '-h', '-c', 'hiera.yaml', 'config',
                     'environment=%s' % args.environment,
                     'site=%s' % args.site,
                     'job=%s' % args.job]

    tempest_init = ['tempest', 'init']

    execute(tempest_init, cwd=args.workdir)
    yaml_config = execute(hiera_command,
                          os.path.dirname(os.path.realpath(__file__)))
    configfile = os.path.join(args.workdir, 'etc', 'tempest.conf')

    write_config(yaml_config=yaml_config, config_file=configfile,
                 environment=args.environment, site=args.site,
                 host=args.host, image=args.image, job=args.job)


if __name__ == '__main__':
    main()
