import os
collectd_server_auth_dir = os.getcwd() + "/data/collectd/server_auth"

pkg_yum = {
    'collectd': {},
    'collectd-curl': {},
    'collectd-curl_json': {},
    'collectd-curl_xml': {},
    'collectd-lvm': {},
    'collectd-netlink': {},
    'rrdtool': {},
}

svc_systemd = {
    'collectd': {
        'enabled': True,
        'needs': [
            "pkg_yum:collectd",
        ],
    },
}

files = {
    '/etc/collectd.conf': {
        'source': "collectd.conf",
        'owner': "root",
        'group': "root",
        'mode': "0644",
        'content_type': "mako",
        'context': {
            'collectd': node.metadata.get('collectd', {}),
        },
        'needs': [
            "pkg_yum:collectd",
        ],
        'triggers': [
            "svc_systemd:collectd:restart",
        ],
    },
}

actions = {}

directories = {
    "/etc/collectd/plugins": {
        "mode": "0755",
        "owner": "root",
        "group": "root",
        'needs': [
            "pkg_yum:collectd",
        ],
    },
}

git_deploy = {}

if node.metadata.get('collectd', {}).get('write_rrd', True):
    pkg_yum['collectd-rrdtool'] = {
        'triggers': [
            "svc_systemd:collectd:restart",
        ],
    }

if node.metadata.get('collectd', {}).get('client'):
    files['/etc/collectd.d/client.conf'] = {
        'source': "client.conf",
        'owner': "root",
        'group': "root",
        'mode': "0640",
        'content_type': "mako",
        'context': {
            'client': node.metadata.get('collectd', {}).get('client', {}),
        },
        'needs': [
            "pkg_yum:collectd",
        ],
        'triggers': [
            "svc_systemd:collectd:restart",
        ],
    }

if node.metadata.get('collectd', {}).get('server'):
    files['/etc/collectd.d/server.conf'] = {
        'source': "server.conf",
        'owner': "root",
        'group': "root",
        'mode': "0640",
        'content_type': "mako",
        'context': {
            'server': node.metadata.get('collectd', {}).get('server', {}),
        },
        'needs': [
            "pkg_yum:collectd",
        ],
        'triggers': [
            "svc_systemd:collectd:restart",
        ],
    }

    files['/etc/collectd.d/auth_file'] = {
        'source': "{}/{}.auth".format(collectd_server_auth_dir, node.name),
        'owner': "root",
        'group': "root",
        'mode': "0640",
        'needs': [
            "pkg_yum:collectd",
        ],
        'triggers': [
            "svc_systemd:collectd:restart",
        ],
    }

    if node.has_bundle("firewalld"):
        port = node.metadata.get('collectd', {}).get('server', {}).get('port', "25826")
        if node.metadata.get('collectd', {}).get('server', {}).get('firewalld_permitted_zone'):
            zone = node.metadata.get('collectd', {}).get('server', {}).get('firewalld_permitted_zone')
            actions['firewalld_add_collectd_zone_{}'.format(zone)] = {
                'command': "firewall-cmd --permanent --zone={} --add-port={}/udp".format(zone, port),
                'unless': "firewall-cmd --zone={} --list-ports | grep {}/udp".format(zone, port),
                'cascade_skip': False,
                'needs': [
                    "pkg_yum:firewalld",
                ],
                'triggers': [
                    "action:firewalld_reload",
                ],
            }
        elif node.metadata.get('firewalld', {}).get('default_zone'):
            default_zone = node.metadata.get('firewalld', {}).get('default_zone')
            actions['firewalld_add_collectd_zone_{}'.format(default_zone)] = {
                'command': "firewall-cmd --permanent --zone={} --add-port={}/udp".format(default_zone, port),
                'unless': "firewall-cmd --zone={} --list-ports | grep {}/udp".format(default_zone, port),
                'cascade_skip': False,
                'needs': [
                    "pkg_yum:firewalld",
                ],
                'triggers': [
                    "action:firewalld_reload",
                ],
            }
        elif node.metadata.get('firewalld', {}).get('custom_zones', False):
            for interface in node.metadata['interfaces']:
                custom_zone = node.metadata.get('interfaces', {}).get(interface).get('firewalld_zone')
                actions['firewalld_add_collectd_zone_{}'.format(custom_zone)] = {
                    'command': "firewall-cmd --permanent --zone={} --add-port={}/udp".format(custom_zone, port),
                    'unless': "firewall-cmd --zone={} --list-ports | grep {}/udp".format(custom_zone, port),
                    'cascade_skip': False,
                    'needs': [
                        "pkg_yum:firewalld",
                    ],
                    'triggers': [
                        "action:firewalld_reload",
                    ],
                }
        else:
            actions['firewalld_add_https'] = {
                'command': "firewall-cmd --permanent --add-port={}/udp".format(port),
                'unless': "firewall-cmd --list-ports | grep {}/udp".format(port),
                'cascade_skip': False,
                'needs': [
                    "pkg_yum:firewalld",
                ],
                'triggers': [
                    "action:firewalld_reload",
                ],
            }

if node.metadata.get('collectd', {}).get('cgp', {}):
    cgp_install_path = node.metadata.get('collectd', {}).get('cgp', {}).get('install_path')
    directories['{}'.format(cgp_install_path)] = {
        "mode": "0755",
    }

    git_deploy['{}'.format(cgp_install_path)] = {
        'needs': [
            "directory:{}".format(cgp_install_path)
        ],
        'repo': "https://github.com/pommi/CGP.git",
        'rev': "master",
    }

    files['{}/conf/config.local.php'.format(cgp_install_path)] = {
        'source': "cgp_config",
        'owner': "root",
        'group': "root",
        'mode': "0644",
        'needs': [
            "git_deploy:{}".format(cgp_install_path)
        ],
    }
