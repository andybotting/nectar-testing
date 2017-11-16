# Generating a Tempest config file

Configuration is stored in yaml in the `config` directory.

We use *Hiera* from Puppetlabs to generate the configuration options we need
specific to the job/site/environment.

 * Job specific config should go in     `config/jobs/<name>.yaml`
 * Site specific in                     `config/sites/<site>.yaml`
 * Environment (production/testing etc) `config/environments/<environment>.yaml`
 * Defaults                             `config/defaults.yaml`

Check out the hierarchy in `hiera.yaml`

An example hiera call to see what the config would be:
`hiera -f yaml -h -c hiera.yaml config environment=production site=site-a job=check_cinder`

## setup_tempest.py
This script will run tempest init then using the generated tempest.conf pull in the
config from the hiera command and add it to the tempest.conf

Example:
```
 mkdir /tmp/tempest_run/
 ./setup_tempest.py --host -s site-a -e production -j check-compute-host /tmp/tempest_run
```

## Running test
Go to the tempest run dir

 `cd /tmp/tempest_run/`

Run one test

 `ostestr -n tempest.api.compute.servers.test_create_server.ServersTestJSON.test_host_name_is_same_as_server_name`

## Whitelists
These are all stored in the whitelists directory
