# bundlewrap-collectd

`bundlewrap-collectd` install and configures [collectd](https://collectd.org/), "a daemon which collects system and application performance metrics periodically and provides mechanisms to store the values in a variety of ways".
By default data is being stored in RRD files.
Additionally it's possible to configure collectd as server as well as client to send data encrypted to another instance.

## Compatibility

This bundle has been tested on the following systems:

| OS          | `[x]` |
| ----------- | ----- |
| Fedora 24   | `[x]` |
| Fedberry 24 | `[x]` |

## Integrations

## Integrations

* Bundles:
  * [firewalld](https://github.com/rullmann/bundlewrap-firewalld)
    * Zone settings from firewalld bundle will be used, if you do not overwrite this behaviour in the metdata.

## Metadata

    'metadata': {
        'collectd': {
            'interval': "10", # optional, defaults to 10
            'collect_internal_stats': True, # optional, `False` by default
            'server': { # off by default
                'ip': "10.11.12.13",
                'port': "25826", # optional, defaults to 25826
                'firewalld_permitted_zone': "internal", # optional, only used when firewalld bundle is used
            },
            'client': { # off by default
                'ip': "10.11.12.13", # your servers ip address!
                'port': "25826", # optional, defaults to 25826
                'user': "username",
                'password': "secret",
            },
        },
    }

## Notes

### Server configuration

Using the server requires a data dir: `<bwrepo>/data/collectd/server_auth`
Within this dir the authentication file will be stored. Please find additional information about these files in the [collectd wiki](https://collectd.org/wiki/index.php/Networking_introduction#Cryptographic_setup).

Please check if your server IP is matching firewalld Zone setting. If not please use the `firewalld_allowed_zone` setting.
