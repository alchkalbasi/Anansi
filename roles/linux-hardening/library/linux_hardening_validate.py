#!/usr/bin/python
# SPDX-License-Identifier: Apache-2.0
from ansible.module_utils.basic import AnsibleModule
import re
BOOLEAN_NAMES = ['linux_hardening_selinux_enabled',
 'ssh_hardening_selinux_install_packages',
 'ssh_hardening_selinux_ports_enabled',
 'ssh_hardening_selinux_remove_password_policy',
 'linux_hardening_login_defs_permissions',
 'linux_hardening_sysctl_permissions',
 'linux_hardening_auditd_permissions',
 'linux_hardening_disable_core_dumps',
 'linux_hardening_disable_ctrl_alt_del',
 'linux_hardening_cron_permissions',
 'linux_hardening_shadow_permissions',
 'linux_hardening_passwd_permissions',
 'linux_hardening_restrict_su',
 'linux_hardening_minimize_path_permissions',
 'linux_hardening_remove_insecure_packages',
 'linux_hardening_remove_pam_ccreds',
 'linux_hardening_pam_passwdqc',
 'linux_hardening_pam_faillock',
 'linux_hardening_pam_no_pass_expiry',
 'linux_hardening_libuser_hash',
 'linux_hardening_securetty',
 'linux_hardening_shell_timeout',
 'linux_hardening_shell_umask',
 'linux_hardening_remove_rhosts',
 'linux_hardening_remove_hosts_equiv',
 'linux_hardening_remove_netrc',
 'linux_hardening_suid_blacklist_enabled',
 'linux_hardening_suid_remove_unknown',
 'linux_hardening_system_account_shells',
 'linux_hardening_system_account_lock',
 'linux_hardening_user_password_ageing',
 'linux_hardening_root_password_ageing',
 'linux_hardening_remove_duplicate_root',
 'linux_hardening_root_home_permissions',
 'linux_hardening_user_home_permissions',
 'linux_hardening_auditd_install',
 'linux_hardening_auditd_service',
 'linux_hardening_disable_journald_audit',
 'linux_hardening_kernel_parameters',
 'linux_hardening_refresh_initramfs',
 'ssh_hardening_install_server',
 'ssh_hardening_install_client',
 'ssh_hardening_enable_service',
 'ssh_hardening_disable_pam_motd',
 'ssh_hardening_regenerate_rsa_key',
 'ssh_hardening_host_key_permissions',
 'ssh_hardening_filter_moduli',
 'ssh_hardening_server_config_permissions',
 'ssh_hardening_client_config_permissions',
 'iptables_hardening_enabled',
 'iptables_hardening_install_packages',
 'iptables_hardening_persistent',
 'iptables_hardening_ipv4_enabled',
 'iptables_hardening_ipv6_enabled',
 'iptables_hardening_default_input_policy_enabled',
 'iptables_hardening_default_output_policy_enabled',
 'iptables_hardening_default_forward_policy_enabled',
 'iptables_hardening_allow_loopback',
 'iptables_hardening_allow_established',
 'iptables_hardening_allow_ssh',
 'iptables_hardening_allow_icmp',
 'iptables_hardening_drop_invalid',
 'iptables_hardening_anti_spoofing',
 'iptables_hardening_log_dropped',
 'iptables_hardening_allow_custom_tcp_ports',
 'iptables_hardening_allow_custom_udp_ports',
 'iptables_hardening_allow_outbound_tcp_ports',
 'iptables_hardening_allow_outbound_udp_ports']

def validate(settings):
    for key in BOOLEAN_NAMES:
        if type(settings[key]) is not bool:
            raise ValueError(key + ' must be a YAML boolean (true or false), not a string')
    def nested(value, path):
        if isinstance(value, dict):
            for key, child in value.items():
                if key in ('enabled', 'permissions_enabled') and type(child) is not bool:
                    raise ValueError(path + '.' + key + ' must be a YAML boolean')
                nested(child, path + '.' + key)
        elif isinstance(value, list):
            for child in value:
                nested(child, path)
    nested(settings, 'settings')
    for key, enabled in settings['linux_hardening_modules'].items():
        if type(enabled) is not bool or not re.fullmatch('[a-z0-9_-]+', key):
            raise ValueError('Invalid module control: ' + key)
    for name in ('linux_hardening_login_defs', 'linux_hardening_sysctl_settings',
                 'linux_hardening_faillock_settings', 'linux_hardening_auditd_settings',
                 'ssh_hardening_server_directives', 'ssh_hardening_client_directives'):
        for key, control in settings[name].items():
            if not isinstance(control, dict) or type(control.get('enabled')) is not bool or 'value' not in control:
                raise ValueError(name + '.' + key + ' requires enabled: boolean and value')
            if not re.fullmatch('[A-Za-z0-9_.]+', key):
                raise ValueError('Invalid setting name: ' + key)
            if control['enabled'] and isinstance(control['value'], str) and any(c in control['value'] for c in ('\n', '\r')):
                raise ValueError('Multiline setting values are forbidden: ' + key)
    if settings['iptables_hardening_enabled']:
        for key in ('iptables_hardening_ssh_port',):
            if type(settings[key]) is not int or not 1 <= settings[key] <= 65535:
                raise ValueError('Invalid TCP port: ' + key)
        for name, gate in [('tcp_ports','allow_custom_tcp_ports'), ('udp_ports','allow_custom_udp_ports'),
                           ('outbound_tcp_ports','allow_outbound_tcp_ports'), ('outbound_udp_ports','allow_outbound_udp_ports')]:
            if settings['iptables_hardening_' + gate]:
                for port in settings['iptables_hardening_' + name]:
                    if type(port) is not int or not 1 <= port <= 65535:
                        raise ValueError('Port lists require integers in 1..65535')
        if not re.fullmatch(r'[1-9][0-9]*/(second|minute|hour|day|sec|min)',settings['iptables_hardening_log_rate']):
            raise ValueError('Invalid firewall log rate')
        if type(settings['iptables_hardening_log_burst']) is not int or settings['iptables_hardening_log_burst'] < 1:
            raise ValueError('Invalid firewall log burst')
    if not re.fullmatch('[0-7]{3,4}', settings['linux_hardening_umask']):
        raise ValueError('Invalid shell umask')
    if type(settings['linux_hardening_shell_timeout_seconds']) is not int or settings['linux_hardening_shell_timeout_seconds'] < 1:
        raise ValueError('Shell timeout must be a positive integer')

def main():
    module = AnsibleModule(argument_spec=dict(settings=dict(type='dict',required=True)),supports_check_mode=True)
    try:
        validate(module.params['settings'])
    except (ValueError, KeyError, TypeError) as error:
        module.fail_json(msg=str(error))
    module.exit_json(changed=False)
if __name__ == '__main__':
    main()
