# Nectar Tempest testing for Nagios

We assume you've got a Python 3 virtualenv set up in /opt/tempest with
[Tempest](https://github.com/openstack/tempest) installed within it.

In the `tempest_nagios.conf` file, you can define your environment settings.

For example, this is an example for a production environment.
```
[settings:production]
nagios_token = <password>
nagios_url = https://nagios.your.site/nrdp/
nagios_test_hostname = tempest.your.site
```
 * `nagios_token` is the token to submit test results to Nagios via NRDP
 * `nagios_url` is the NRDP URL to send the results to
 * `nagios_test_hostname` is the hostname to pass in the NRDP results. The
   results will be tied to a Nagios service under this host. You will need
   to pre-create these in Nagios first.

The tests section provides a name for a particular test you'd like to run.
For example, we have:

```
[tests]
compute = tempest.api.compute.servers.test_create_server.ServersTestJSON.test_verify_created_server_vcpus
network = tempest.scenario.test_network_basic_ops.TestNetworkBasicOps.test_network_basic_ops
```

The Nagios service name will include this test name for posting the results,
which we make some assumtions about.

It's usually `nagios_<site>_<test>`


```
usage: tempest_nagios.py [-h] [-c CONFIG] [-v] -e ENVIRONMENT [-f FLAVOR]
                         [-o OUTPUT] [-s SITE] [-t TEST]

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        Nagios settings config file
  -v, --verbose         Verbose
  -e ENVIRONMENT, --environment ENVIRONMENT
                        Set the environment
  -f FLAVOR, --flavor FLAVOR
                        Set test flavor
  -o OUTPUT, --output OUTPUT
                        Output config file
  -s SITE, --site SITE  site for configuration
  -t TEST, --test TEST  test to run
```

To run the compute test for site-a in production, we would run:

```
. /opt/tempest/bin/activate  # activate the virtualenv
/opt/nectar-testing/nagios/tempest_nagios.py -c /opt/nectar-testing/nagios/tempest_nagios.conf -s site-a -t compute -e production
```

We also include a `tempest_purge.py` script for calling out to
[ospurge](https://github.com/openstack/ospurge) for cleaning up a project
if the Tempest tests haven't exited gracefully.

You'll need to also install that into your virtualenv for this to work.
