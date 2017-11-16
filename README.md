# Nectar testing

This is a collection of scripts used by the Nectar Research Cloud for monitoring
and testing with Tempest.

The `nagios` directory contains scripts used for regular periodic testing of
sites and services on our cloud infrastructure.

The `tempest` directory contains code used for generating tempest configuration
files with site/job/environment specific settings along with individual
authentication settings (usename, password, project).

See the README.md file in each directory for more information.

It is very likely these scripts will need to be modified for your environment as
we've made plenty of assumptions with this code. Having said that, we hope this
is useful if you're interested in using Tempest for monitoring an OpenStack
setup.

Feel free to contact me at andrew.botting@unimelb.edu.au for any questions!
