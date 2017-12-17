pkg_dnf = {
    'collectd': {},
    'collectd-chrony': {},
    'collectd-curl': {},
    'collectd-curl_json': {},
    'collectd-curl_xml': {},
    'collectd-netlink': {},
    'rrdtool': {},
}

if node.os == 'fedora' and node.os_version >= (26):
    pkg_dnf['collectd-disk'] = {}

svc_systemd = {
    'collectd': {
        'needs': ['pkg_dnf:collectd'],
    },
}

files = {
    '/etc/collectd.conf': {
        'source': 'collectd.conf',
        'mode': '0600',
        'content_type': 'mako',
        'context': {
            'collectd': node.metadata.get('collectd', {}),
        },
        'needs': ['pkg_dnf:collectd', 'pkg_dnf:rrdtool'],
        'triggers': ['svc_systemd:collectd:restart'],
    },
    '/etc/collectd.d/nut.conf': {
        'delete': True,
        'needs': ['pkg_dnf:collectd'],
    },
}

actions = {}

directories = {
    '/etc/collectd.d/plugins': {
        'mode': '0755',
        'needs': ['pkg_dnf:collectd'],
    },
    '/etc/collectd.d/types': {
        'mode': '0755',
        'needs': ['pkg_dnf:collectd'],
    },
}

git_deploy = {}

if node.metadata.get('collectd', {}).get('write_rrd', True):
    pkg_dnf['collectd-rrdtool'] = {
        'triggers': ['svc_systemd:collectd:restart'],
    }

if node.metadata.get('collectd', {}).get('client'):
    files['/etc/collectd.d/client.conf'] = {
        'source': 'client.conf',
        'mode': '0600',
        'content_type': 'mako',
        'context': {
            'client': node.metadata.get('collectd', {}).get('client', {}),
        },
        'needs': ['pkg_dnf:collectd'],
        'triggers': ['svc_systemd:collectd:restart'],
    }

if node.metadata.get('collectd', {}).get('server'):
    files['/etc/collectd.d/server.conf'] = {
        'source': 'server.conf',
        'mode': '0600',
        'content_type': 'mako',
        'context': {
            'server': node.metadata.get('collectd', {}).get('server', {}),
        },
        'needs': ['pkg_dnf:collectd'],
        'triggers': ['svc_systemd:collectd:restart'],
    }

    files['/etc/collectd.d/collectd.auth'] = {
        'source': 'server_auth/{}.auth'.format(node.name),
        'mode': '0600',
        'needs': ['pkg_dnf:collectd'],
        'triggers': ['svc_systemd:collectd:restart'],
    }

    if node.has_bundle('firewalld'):
        port = node.metadata.get('collectd', {}).get('server', {}).get('port', '25826')
        if node.metadata.get('collectd', {}).get('server', {}).get('firewalld_permitted_zone'):
            zone = node.metadata.get('collectd', {}).get('server', {}).get('firewalld_permitted_zone')
            actions['firewalld_add_collectd_zone_{}'.format(zone)] = {
                'command': 'firewall-cmd --permanent --zone={} --add-port={}/udp'.format(zone, port),
                'unless': 'firewall-cmd --zone={} --list-ports | grep {}/udp'.format(zone, port),
                'cascade_skip': False,
                'needs': ['pkg_dnf:firewalld'],
                'triggers': ['action:firewalld_reload'],
            }
        elif node.metadata.get('firewalld', {}).get('default_zone'):
            default_zone = node.metadata.get('firewalld', {}).get('default_zone')
            actions['firewalld_add_collectd_zone_{}'.format(default_zone)] = {
                'command': 'firewall-cmd --permanent --zone={} --add-port={}/udp'.format(default_zone, port),
                'unless': 'firewall-cmd --zone={} --list-ports | grep {}/udp'.format(default_zone, port),
                'cascade_skip': False,
                'needs': ['pkg_dnf:firewalld'],
                'triggers': ['action:firewalld_reload'],
            }
        elif node.metadata.get('firewalld', {}).get('custom_zones', False):
            for interface in node.metadata['interfaces']:
                custom_zone = node.metadata.get('interfaces', {}).get(interface).get('firewalld_zone')
                actions['firewalld_add_collectd_zone_{}'.format(custom_zone)] = {
                    'command': 'firewall-cmd --permanent --zone={} --add-port={}/udp'.format(custom_zone, port),
                    'unless': 'firewall-cmd --zone={} --list-ports | grep {}/udp'.format(custom_zone, port),
                    'cascade_skip': False,
                    'needs': ['pkg_dnf:firewalld'],
                    'triggers': ['action:firewalld_reload'],
                }
        else:
            actions['firewalld_add_https'] = {
                'command': 'firewall-cmd --permanent --add-port={}/udp'.format(port),
                'unless': 'firewall-cmd --list-ports | grep {}/udp'.format(port),
                'cascade_skip': False,
                'needs': ['pkg_dnf:firewalld'],
                'triggers': ['action:firewalld_reload'],
            }

if node.metadata.get('collectd', {}).get('cgp', {}):
    cgp_install_path = node.metadata.get('collectd', {}).get('cgp', {}).get('install_path')
    directories['{}'.format(cgp_install_path)] = {
        'mode': '0755',
    }

    git_deploy['{}'.format(cgp_install_path)] = {
        'needs': [
            'directory:{}'.format(cgp_install_path)
        ],
        'repo': 'https://github.com/pommi/CGP.git',
        'rev': 'master',
    }

    files['{}/conf/config.local.php'.format(cgp_install_path)] = {
        'source': 'cgp_config',
        'mode': '0644',
        'needs': ['git_deploy:{}'.format(cgp_install_path)],
    }

if node.has_bundle('monit'):
    files['/etc/monit.d/collectd'] = {
        'source': 'monit',
        'mode': '0600',
        'content_type': 'mako',
        'context': {
            'server': node.metadata.get('collectd', {}).get('server', {}),
        },
        'triggers': ['svc_systemd:monit:restart'],
    }
