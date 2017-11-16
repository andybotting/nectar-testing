#!/usr/bin/env python
from __future__ import print_function

import argparse
import ast
import configparser
import os
import re
import requests
import shutil
import subprocess
import sys
import tempfile

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET


# We expect a virtualenv created for tempest here
VIRTUALENV = '/opt/tempest'
VERBOSE = False


def post_nagios_result(url, token, xml):
    params = {'token': token.strip(),
              'cmd': 'submitcheck',
              'XMLDATA': xml}
    result = None
    try:
        response = requests.post(url, params=params)
        result = ET.ElementTree(ET.fromstring(response.text))
    except Exception as e:
        print("ERROR: Cannot connect to Nagios NRDP URL %s: %s" % (url, e))

    if result:
        xml = result.getroot()
        print("NRDP Returned: %s" % xml.find('message').text)


def send_result(check_name, status, output, hostname, url, token):
    checkresults = ET.Element('checkresults')
    checkresult = ET.SubElement(checkresults, 'checkresult',
                                type='service', checktype='1')
    ET.SubElement(checkresult, 'hostname').text = hostname
    ET.SubElement(checkresult, 'servicename').text = check_name
    ET.SubElement(checkresult, 'state').text = str(status)
    ET.SubElement(checkresult, 'output').text = output
    xml = ET.tostring(checkresults, 'utf-8')
    post_nagios_result(url, token, xml)


def execute(command, cwd=None):
    output = []
    # Filter out some Python Warnings from Python 3
    # Mostly unit test warnings we can't hide any other way
    patterns = [
        re.compile(': \w+Warning: '),
        re.compile('self._sock = None'),
    ]
    popen = subprocess.Popen(command, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, cwd=cwd)
    for line in iter(popen.stdout.readline, b''):
        cleanline = line.strip().decode('utf-8')
        if not any(r.search(cleanline) for r in patterns):
            output.append(cleanline)
            print(cleanline, file=sys.stdout)
    popen.wait()
    return popen, output


def parse_output(results):
    """Parse the test output

    We do some dirty regex parsing of the output to extract some
    interesting information for the Nagios alert.

    In the result of a failure, we can match some expected lines
    and pass them through to the Nagios alert for the operators
    to see.
    """
    r = re.compile('^Ran: \d tests in (\d+(\.\d*)?|\.\d+) sec\.$')
    tests_time = float(''.join([m.group(1) for l in results
                                for m in [r.search(l)] if m]))

    # Match the Passed, Skipped, Failed lines
    r = re.compile('^- (\w+): (\d+)$')
    stat_pieces = [m.groups() for l in results
                   for m in [r.search(l)] if m]
    stats = ', '.join([': '.join(s) for s in stat_pieces])

    # Any error details
    pattern = re.compile(
        '^(?:b["\'])Details: (.*)(?:["\'])|'
        '(?:b["\'])AssertionError: .*: (.*)(?:["\'])|'
        '(?:b["\'])tempest\.(?:.*\.)exceptions\..*: (.*)(?:["\'])$',
        re.MULTILINE)

    messages = []
    matches = [y for x in pattern.findall('\n'.join(results)) for y in x if y]

    for m in matches:
        if m.find('message') > -1:
            # Attempt to parse Python dict 'message' if exists
            try:
                error_message = ast.literal_eval(m)
                m = error_message.get('message')
            except Exception:
                pass

        if m not in messages:
            messages.append(m)

    # Build final string
    details = ', '.join(messages)
    output = "Test(s) %s in %0.1fs %s" % (stats, tests_time, details)
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config',
                        default='tempest_nagios.conf',
                        help='Nagios settings config file')
    parser.add_argument('-v', '--verbose',
                        action='store_true',
                        help='Verbose')
    parser.add_argument('-e', '--environment', required=True,
                        help='Set the environment')
    parser.add_argument('-f', '--flavor',
                        default=None,
                        help='Set test flavor')
    parser.add_argument('-o', '--output',
                        default='etc/tempest.conf',
                        help='Output config file')
    parser.add_argument('-s', '--site', action='store',
                        help='site for configuration')
    parser.add_argument('-t', '--test', action='store',
                        help='test to run')

    args = parser.parse_args()

    if args.verbose:
        global VERBOSE
        VERBOSE = True

    if not args.test:
        raise ValueError('Need to provide a test')

    if not os.path.isfile(args.config):
        raise ValueError('Settings config file "%s" not found' % args.config)

    config = configparser.ConfigParser()
    config.read(args.config)

    environment = args.environment

    # Nagios NRDP settings from config file
    section = 'settings:%s' % environment
    env_settings = dict(config.items(section))
    nagios_token = env_settings.get('nagios_token')
    nagios_url = env_settings.get('nagios_url')
    check_hostname = env_settings.get('nagios_test_hostname')

    # Make our working directory
    test_path = tempfile.mkdtemp(prefix='tempest_')

    # Make job and test name
    if args.flavor:
        job = 'nagios' + '_' + environment + '_' + args.flavor
    else:
        job = 'nagios' + '_' + args.test

    # Run tempest
    base_path = os.path.dirname(os.path.realpath(__file__))
    cmd_setup = ['./setup_tempest.py', '-e', environment,
                 '-j', job, test_path]
    if args.site:
        cmd_setup.append('-s')
        cmd_setup.append(args.site)

    popen, output = execute(cmd_setup,
                            cwd=os.path.join(base_path, '../tempest/'))
    return_code = popen.returncode
    if return_code:
        print('setup_tempest return error: %s' % return_code)
        sys.exit(return_code)

    test_id = config.get('tests', args.test)
    cmd_run = ['ostestr', '--serial', '-n', test_id]

    popen, output = execute(cmd_run, cwd=test_path)
    return_code = popen.returncode

    # Delete working directory
    shutil.rmtree(test_path)

    test_output = parse_output(output)

    if return_code > 0:
        status = 2  # Critical
    else:
        status = 0  # OK!

    # Construct the Nagios Check Name
    name_pieces = ['tempest']
    if args.site:
        name_pieces.append(args.site)
    if args.flavor:
        name_pieces.append(args.flavor)
    if args.test:
        name_pieces.append(args.test)

    nagios_check_name = '_'.join(name_pieces)

    print("Sending result to NRDP: %s: %s" % (nagios_check_name, test_output))

    # Post result
    send_result(nagios_check_name, status, test_output, check_hostname,
                nagios_url, nagios_token)

    # Nagios exit
    sys.exit(status)


if __name__ == '__main__':
    main()
