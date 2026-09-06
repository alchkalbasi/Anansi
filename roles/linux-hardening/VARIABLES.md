# Complete variable reference

All booleans below default to false. Lists and values never activate a control. Only actual YAML booleans are accepted. The exact machine-readable definitions are in [defaults/main.yml](defaults/main.yml).

## Scalar switches and values

| Variable | Default | Effect / units |
| --- | --- | --- |
| `linux_hardening_disable_core_dumps` | `false` | Disable PAM hard/soft core limits, systemd storage/processing, and shell core limits. |
| `linux_hardening_disable_ctrl_alt_del` | `false` | Mask the systemd console reboot shortcut. |
| `linux_hardening_cron_permissions` | `false` | Restrict existing cron configuration ownership and remove group/other access. |
| `linux_hardening_shadow_permissions` | `false` | Set shadow/gshadow and existing backups to root:shadow 0640. |
| `linux_hardening_passwd_permissions` | `false` | Set passwd/group and existing backups to root:root 0644. |
| `linux_hardening_restrict_su` | `false` | Restrict /bin/su to root:root 0750; review group access before enabling. |
| `linux_hardening_minimize_path_permissions` | `false` | Remove group/other write access from files in the configured system executable paths. |
| `linux_hardening_remove_insecure_packages` | `false` | Purge the selected Debian package list without autoremove. |
| `linux_hardening_remove_pam_ccreds` | `false` | Remove libpam-ccreds to prevent cached PAM credentials. |
| `linux_hardening_pam_passwdqc` | `false` | Install and enable Debian passwdqc with the selected strength parameters. |
| `linux_hardening_pam_faillock` | `false` | Install libpam-modules and enable pre-authentication/account and authfail profiles. |
| `linux_hardening_pam_no_pass_expiry` | `false` | Add no_pass_expiry to the existing pam_unix account line. |
| `linux_hardening_libuser_hash` | `false` | Set the libuser crypt_style INI key for hosts using libuser. |
| `linux_hardening_securetty` | `false` | Write the allowed local root terminal list to /etc/securetty. |
| `linux_hardening_shell_timeout` | `false` | Install a readonly login-shell idle timeout. |
| `linux_hardening_shell_umask` | `false` | Install a login-shell umask profile. |
| `linux_hardening_remove_rhosts` | `false` | Remove .rhosts from each local account home. |
| `linux_hardening_remove_hosts_equiv` | `false` | Remove /etc/hosts.equiv. |
| `linux_hardening_remove_netrc` | `false` | Remove .netrc from local homes except the named exemptions. |
| `linux_hardening_suid_blacklist_enabled` | `false` | Remove SUID/SGID from existing blacklisted binaries. |
| `linux_hardening_suid_remove_unknown` | `false` | Scan the root filesystem and remove SUID/SGID outside the whitelist. |
| `linux_hardening_system_account_shells` | `false` | Set selected non-root system accounts to /usr/sbin/nologin. |
| `linux_hardening_system_account_lock` | `false` | Lock selected system account passwords without replacing their hashes. |
| `linux_hardening_user_password_ageing` | `false` | Set minimum/maximum/warning ages for unlocked regular accounts. |
| `linux_hardening_root_password_ageing` | `false` | Set minimum/maximum/warning ages for unlocked UID-zero accounts. |
| `linux_hardening_remove_duplicate_root` | `false` | Delete accounts with UID 0 whose name is not root. |
| `linux_hardening_root_home_permissions` | `false` | Set UID-zero account homes to owner-only 0700. |
| `linux_hardening_user_home_permissions` | `false` | Set regular account homes to owner-only 0700, subject to exemptions. |
| `linux_hardening_auditd_install` | `false` | Install auditd without a package-triggered start. |
| `linux_hardening_auditd_service` | `false` | Start and enable auditd; configuration changes independently notify restart. |
| `linux_hardening_disable_journald_audit` | `false` | Stop, disable, and mask the journald audit socket; restart journald only on change. |
| `linux_hardening_kernel_parameters` | `false` | Master permission for sysctl operations; each key also needs enabled: true. |
| `linux_hardening_refresh_initramfs` | `false` | Allow update-initramfs -u only when an enabled module policy file changes. |
| `linux_hardening_path_directories` | `["/usr/local/sbin", "/usr/local/bin", "/usr/sbin", "/usr/bin", "/sbin", "/bin"]` | Absolute executable directories inspected by minimize_path_permissions; find follows command-line directory symlinks. |
| `linux_hardening_insecure_packages` | `["xinetd", "openbsd-inetd", "inetutils-inetd", "nis", "telnetd", "inetutils-telnetd", "rsh-server", "rsh-redone-server", "prelink"]` | Debian apt package names removed only by remove_insecure_packages. |
| `linux_hardening_passwdqc_options` | `"min=disabled,disabled,16,12,8"` | Native pam_passwdqc options; applied only by pam_passwdqc. |
| `linux_hardening_libuser_hash_value` | `"sha512"` | Native libuser crypt_style value; does not rehash existing passwords. |
| `linux_hardening_root_ttys` | `["console", "tty1", "tty2", "tty3", "tty4", "tty5", "tty6"]` | Terminal names permitted by the securetty control. |
| `linux_hardening_shell_timeout_seconds` | `600` | Positive idle timeout in seconds; no effect without shell_timeout. |
| `linux_hardening_umask` | `"027"` | Quoted octal umask for the shell profile; login.defs UMASK is independently managed. |
| `linux_hardening_netrc_users_exempt` | `[]` | Local usernames whose .netrc is preserved. |
| `linux_hardening_users_exempt` | `["root", "sync", "shutdown", "halt"]` | Local usernames excluded from system-account and regular-account hardening. Root-specific controls are separate. |
| `linux_hardening_home_users_exempt` | `[]` | Usernames excluded from root and regular home-permission changes. |
| `linux_hardening_age_users_exempt` | `[]` | Usernames excluded from password ageing. |
| `linux_hardening_system_uid_max` | `999` | Maximum positive UID classified as a system account. |
| `linux_hardening_uid_min` | `1000` | Minimum UID classified as a regular account. |
| `linux_hardening_uid_max` | `60000` | Maximum UID classified as a regular account. |
| `linux_hardening_password_min_age` | `7` | Minimum days between password changes for enabled account-ageing controls. |
| `linux_hardening_password_max_age` | `60` | Maximum password age in days for enabled account-ageing controls. |
| `linux_hardening_password_warn_age` | `7` | Warning days before password expiry. |
| `linux_hardening_suid_blacklist` | `["/usr/bin/rcp", "/usr/bin/rlogin", "/usr/bin/rsh", "/usr/lib/openssh/ssh-keysign", "/usr/sbin/pppd", "/usr/bin/lockfile", "/usr/bin/mail-lock", "/usr/bin/mail-unlock", "/usr/bin/mail-touchlock", "/usr/bin/dotlockfile", "/usr/bin/arping", "/usr/sbin/uuidd", "/usr/bin/mtr", "/usr/lib/evolution/camel-lock-helper-1.2", "/usr/lib/pt_chown", "/usr/lib/eject/dmcrypt-get-device", "/usr/lib/mc/cons.saver"]` | Existing binary paths whose SUID/SGID bits are removed only when its blacklist gate is true. |
| `linux_hardening_suid_whitelist` | `["/bin/mount", "/bin/ping", "/bin/su", "/usr/bin/su", "/bin/umount", "/sbin/pam_timestamp_check", "/sbin/unix_chkpwd", "/usr/bin/at", "/usr/bin/gpasswd", "/usr/bin/locate", "/usr/bin/newgrp", "/usr/bin/passwd", "/usr/bin/ssh-agent", "/usr/sbin/lockdev", "/usr/bin/expiry", "/bin/ping6", "/usr/bin/traceroute6.iputils", "/sbin/mount.nfs", "/sbin/umount.nfs", "/sbin/mount.nfs4", "/sbin/umount.nfs4", "/usr/bin/crontab", "/usr/bin/wall", "/usr/bin/write", "/usr/bin/screen", "/usr/bin/mlocate", "/usr/bin/chage", "/usr/bin/chfn", "/usr/bin/chsh", "/bin/fusermount", "/usr/bin/pkexec", "/usr/bin/sudo", "/usr/bin/sudoedit", "/usr/sbin/postdrop", "/usr/sbin/postqueue", "/usr/sbin/suexec", "/usr/lib/squid/ncsa_auth", "/usr/lib/squid/pam_auth", "/usr/sbin/ccreds_validate", "/usr/bin/Xorg", "/usr/bin/X", "/usr/lib/dbus-1.0/dbus-daemon-launch-helper", "/usr/lib/vte/gnome-pty-helper", "/usr/lib/libvte9/gnome-pty-helper", "/usr/lib/libvte-2.90-9/gnome-pty-helper", "/usr/bin/mount", "/usr/bin/umount", "/usr/bin/ping", "/usr/bin/fusermount3", "/usr/sbin/unix_chkpwd"]` | Allowed SUID/SGID paths for the optional unknown-binary root-filesystem scan. |
| `ssh_hardening_install_server` | `false` | Install openssh-server, suppressing package-triggered service starts. |
| `ssh_hardening_install_client` | `false` | Install openssh-client. |
| `ssh_hardening_enable_service` | `false` | Start and enable the existing ssh service. |
| `ssh_hardening_disable_pam_motd` | `false` | Remove optional pam_motd SSH session entries. |
| `ssh_hardening_regenerate_rsa_key` | `false` | Ensure the RSA host key has the chosen size; can rotate host identity. |
| `ssh_hardening_host_key_permissions` | `false` | Set existing private host keys to root:root 0600. |
| `ssh_hardening_filter_moduli` | `false` | Atomically remove DH groups below the chosen minimum; refuse an empty result. |
| `ssh_hardening_server_config_permissions` | `false` | Set the main sshd configuration to root:root 0600. |
| `ssh_hardening_client_config_permissions` | `false` | Set the main client configuration to root:root 0644. |
| `ssh_hardening_rsa_key_size` | `4096` | RSA host key size in bits. Default 4096; only used when regeneration is enabled. |
| `ssh_hardening_moduli_minimum` | `2048` | Minimum actual DH group size in bits. The moduli size field is one less. |
| `ssh_hardening_banner_src` | `"ssh_banner"` | Banner source in the role's `files/` directory (or an absolute controller path). Copied as root:root 0644 to the enabled `Banner` directive's path. Empty string leaves the remote file unmanaged. |
| `ssh_hardening_connection_test_timeout` | `30` | Seconds allowed for a fresh authenticated connection after SSH reload. |
| `ssh_hardening_rollback_seconds` | `180` | Independent rollback deadline in seconds; must exceed connection-test timeout by more than 60. |
| `iptables_hardening_enabled` | `false` | Master firewall gate; false skips all firewall tasks, packages, persistence and services. |
| `iptables_hardening_install_packages` | `false` | Install iptables; also iptables-persistent when persistence is explicitly enabled. |
| `iptables_hardening_persistent` | `false` | Persist only selected families after verified application and enable boot restoration. |
| `iptables_hardening_ipv4_enabled` | `false` | Permit processing IPv4 filter rules and, if requested, IPv4 persistence. |
| `iptables_hardening_ipv6_enabled` | `false` | Permit processing IPv6 filter rules and, if requested, IPv6 persistence. |
| `iptables_hardening_default_input_policy_enabled` | `false` | Manage the INPUT policy using its separate value. |
| `iptables_hardening_default_output_policy_enabled` | `false` | Manage the OUTPUT policy using its separate value. |
| `iptables_hardening_default_forward_policy_enabled` | `false` | Manage the FORWARD policy using its separate value. |
| `iptables_hardening_allow_loopback` | `false` | Accept loopback input/output. |
| `iptables_hardening_allow_established` | `false` | Accept ESTABLISHED and RELATED input/output/forward traffic. |
| `iptables_hardening_allow_ssh` | `false` | Accept NEW input TCP traffic on the configured SSH port. |
| `iptables_hardening_allow_icmp` | `false` | Accept ICMP or ICMPv6 input/output, including neighbor discovery and PMTU. |
| `iptables_hardening_drop_invalid` | `false` | Drop INVALID conntrack states in INPUT, OUTPUT, and FORWARD. |
| `iptables_hardening_anti_spoofing` | `false` | Drop off-loopback loopback sources and multicast sources on INPUT. |
| `iptables_hardening_log_dropped` | `false` | Rate-limit LOG rules for fallthrough traffic on effective DROP chains. |
| `iptables_hardening_allow_custom_tcp_ports` | `false` | Manage the explicitly listed NEW inbound TCP allowances. |
| `iptables_hardening_allow_custom_udp_ports` | `false` | Manage the explicitly listed NEW inbound UDP allowances. |
| `iptables_hardening_allow_outbound_tcp_ports` | `false` | Manage the explicitly listed NEW outbound TCP allowances. |
| `iptables_hardening_allow_outbound_udp_ports` | `false` | Manage the explicitly listed NEW outbound UDP allowances. |
| `iptables_hardening_default_input_policy` | `"DROP"` | INPUT built-in policy value; only ACCEPT or DROP; ignored while its gate is false. |
| `iptables_hardening_default_output_policy` | `"ACCEPT"` | OUTPUT built-in policy value; only ACCEPT or DROP; ignored while its gate is false. |
| `iptables_hardening_default_forward_policy` | `"DROP"` | FORWARD built-in policy value; only ACCEPT or DROP; ignored while its gate is false. |
| `iptables_hardening_ssh_port` | `22` | Integer TCP management port, 1..65535; match the current ansible_port. |
| `iptables_hardening_tcp_ports` | `[]` | Unique integer inbound TCP destination ports, 1..65535; requires its custom TCP gate. |
| `iptables_hardening_udp_ports` | `[]` | Unique integer inbound UDP destination ports, 1..65535; requires its custom UDP gate. |
| `iptables_hardening_outbound_tcp_ports` | `[]` | Unique integer outbound TCP destination ports, 1..65535; requires its outbound TCP gate. |
| `iptables_hardening_outbound_udp_ports` | `[]` | Unique integer outbound UDP destination ports, 1..65535; requires its outbound UDP gate. |
| `iptables_hardening_log_rate` | `"5/min"` | Positive xtables log rate, e.g. 5/min; only used for enabled logging. |
| `iptables_hardening_log_burst` | `10` | Positive packet burst for the enabled log rate limit. |
| `iptables_hardening_rollback_seconds` | `180` | Independent rollback deadline in seconds; must exceed connection-test timeout by more than 60. |
| `iptables_hardening_connection_test_timeout` | `30` | Seconds allowed for a fresh authenticated connection through the changed firewall. |
| `linux_hardening_login_defs_permissions` | `false` | Set existing /etc/login.defs to root:root 0444. |
| `linux_hardening_sysctl_permissions` | `false` | Set an existing role sysctl file to root:root 0440; does not create it. |
| `linux_hardening_auditd_permissions` | `false` | Set existing auditd.conf to root:root 0640. |
| `linux_hardening_selinux_enabled` | `false` | Set policy and enforcement state on an already provisioned SELinux host. |
| `linux_hardening_selinux_policy` | `"default"` | Already installed SELinux policy name; default is the Debian reference policy name. |
| `linux_hardening_selinux_state` | `"enforcing"` | Requested SELinux state (enforcing, permissive, disabled); applies only with its enable gate. No automatic reboot. |
| `ssh_hardening_selinux_install_packages` | `false` | Install Debian/Ubuntu SELinux Python bindings and management tooling. |
| `ssh_hardening_selinux_ports_enabled` | `false` | Assign ssh_port_t to the configured TCP port list. |
| `ssh_hardening_selinux_ports` | `[22]` | TCP ports labeled ssh_port_t only with the explicit SELinux port gate. |
| `ssh_hardening_selinux_remove_password_policy` | `false` | Remove an installed legacy ssh_password SELinux module. |

## linux_hardening_sysctl_settings

Each key names a sysctl. `enabled: true` plus `linux_hardening_kernel_parameters: true` applies and persists its value. Values are strings accepted by the target kernel. Missing kernel keys fail visibly.

Every listed entry has `enabled: false`; the table gives its `value` default.

| Entry | Default value |
| --- | --- |
| `fs.protected_hardlinks` | `"1"` |
| `fs.protected_symlinks` | `"1"` |
| `fs.protected_fifos` | `"1"` |
| `fs.protected_regular` | `"2"` |
| `fs.suid_dumpable` | `"0"` |
| `kernel.core_uses_pid` | `"1"` |
| `kernel.kptr_restrict` | `"2"` |
| `kernel.kexec_load_disabled` | `"1"` |
| `kernel.sysrq` | `"0"` |
| `kernel.randomize_va_space` | `"2"` |
| `kernel.yama.ptrace_scope` | `"2"` |
| `net.ipv4.ip_forward` | `"0"` |
| `net.ipv6.conf.all.forwarding` | `"0"` |
| `net.ipv4.conf.all.rp_filter` | `"1"` |
| `net.ipv4.conf.default.rp_filter` | `"1"` |
| `net.ipv4.icmp_echo_ignore_broadcasts` | `"1"` |
| `net.ipv4.icmp_ignore_bogus_error_responses` | `"1"` |
| `net.ipv4.icmp_ratelimit` | `"100"` |
| `net.ipv4.icmp_ratemask` | `"88089"` |
| `net.ipv4.tcp_timestamps` | `"0"` |
| `net.ipv4.conf.all.arp_ignore` | `"1"` |
| `net.ipv4.conf.all.arp_announce` | `"2"` |
| `net.ipv4.tcp_rfc1337` | `"1"` |
| `net.ipv4.tcp_syncookies` | `"1"` |
| `net.ipv4.conf.all.shared_media` | `"1"` |
| `net.ipv4.conf.default.shared_media` | `"1"` |
| `net.ipv4.conf.all.accept_source_route` | `"0"` |
| `net.ipv4.conf.default.accept_source_route` | `"0"` |
| `net.ipv6.conf.all.accept_source_route` | `"0"` |
| `net.ipv6.conf.default.accept_source_route` | `"0"` |
| `net.ipv4.conf.all.send_redirects` | `"0"` |
| `net.ipv4.conf.default.send_redirects` | `"0"` |
| `net.ipv4.conf.all.log_martians` | `"1"` |
| `net.ipv4.conf.default.log_martians` | `"1"` |
| `net.ipv4.conf.default.accept_redirects` | `"0"` |
| `net.ipv4.conf.all.accept_redirects` | `"0"` |
| `net.ipv4.conf.all.secure_redirects` | `"0"` |
| `net.ipv4.conf.default.secure_redirects` | `"0"` |
| `net.ipv6.conf.default.accept_redirects` | `"0"` |
| `net.ipv6.conf.all.accept_redirects` | `"0"` |
| `net.ipv6.conf.all.accept_ra` | `"0"` |
| `net.ipv6.conf.default.accept_ra` | `"0"` |
| `net.ipv6.conf.default.router_solicitations` | `"0"` |
| `net.ipv6.conf.all.router_solicitations` | `"0"` |
| `net.ipv6.conf.default.accept_ra_rtr_pref` | `"0"` |
| `net.ipv6.conf.default.accept_ra_pinfo` | `"0"` |
| `net.ipv6.conf.default.accept_ra_defrtr` | `"0"` |
| `net.ipv6.conf.default.autoconf` | `"0"` |
| `net.ipv6.conf.all.autoconf` | `"0"` |
| `net.ipv6.conf.default.dad_transmits` | `"0"` |
| `net.ipv6.conf.default.max_addresses` | `"1"` |
| `vm.mmap_min_addr` | `"65536"` |
| `vm.mmap_rnd_bits` | `"32"` |
| `vm.mmap_rnd_compat_bits` | `"16"` |
| `kernel.unprivileged_userns_clone` | `"0"` |
| `kernel.unprivileged_bpf_disabled` | `"1"` |

## linux_hardening_login_defs

Each key names a login.defs directive. Only its enabled entry is updated; quote octal and yes/no values. A file-wide permissions change has a separate switch.

Every listed entry has `enabled: false`; the table gives its `value` default.

| Entry | Default value |
| --- | --- |
| `MAIL_DIR` | `"/var/mail"` |
| `CREATE_HOME` | `"yes"` |
| `LOG_UNKFAIL_ENAB` | `"no"` |
| `LOG_OK_LOGINS` | `"yes"` |
| `SYSLOG_SU_ENAB` | `"yes"` |
| `SYSLOG_SG_ENAB` | `"yes"` |
| `SU_NAME` | `"su"` |
| `HUSHLOGIN_FILE` | `".hushlogin"` |
| `ENV_SUPATH` | `"PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"` |
| `ENV_PATH` | `"PATH=/usr/local/bin:/usr/bin:/bin"` |
| `TTYGROUP` | `"tty"` |
| `TTYPERM` | `"0600"` |
| `ERASECHAR` | `"0177"` |
| `KILLCHAR` | `"025"` |
| `UMASK` | `"027"` |
| `USERGROUPS_ENAB` | `"yes"` |
| `PASS_MAX_DAYS` | `"60"` |
| `PASS_MIN_DAYS` | `"7"` |
| `PASS_WARN_AGE` | `"7"` |
| `UID_MIN` | `"1000"` |
| `UID_MAX` | `"60000"` |
| `SYS_UID_MIN` | `"100"` |
| `SYS_UID_MAX` | `"999"` |
| `GID_MIN` | `"1000"` |
| `GID_MAX` | `"60000"` |
| `SYS_GID_MIN` | `"100"` |
| `SYS_GID_MAX` | `"999"` |
| `SUB_UID_MIN` | `"100000"` |
| `SUB_UID_MAX` | `"600100000"` |
| `SUB_UID_COUNT` | `"65536"` |
| `SUB_GID_MIN` | `"100000"` |
| `SUB_GID_MAX` | `"600100000"` |
| `SUB_GID_COUNT` | `"65536"` |
| `LOGIN_RETRIES` | `"5"` |
| `LOGIN_TIMEOUT` | `"60"` |
| `CHFN_RESTRICT` | `""` |
| `DEFAULT_HOME` | `"no"` |
| `ENCRYPT_METHOD` | `"YESCRYPT"` |
| `SHA_CRYPT_MIN_ROUNDS` | `"640000"` |
| `SHA_CRYPT_MAX_ROUNDS` | `"640000"` |

## linux_hardening_faillock_settings

Each key names a faillock.conf parameter. These switches manage parameter values independently of enabling the PAM profiles. An empty string value for even_deny_root emits the bare flag; only use true for that entry if root lockout is intended.

Every listed entry has `enabled: false`; the table gives its `value` default.

| Entry | Default value |
| --- | --- |
| `deny` | `"5"` |
| `unlock_time` | `"600"` |
| `even_deny_root` | `""` |

## linux_hardening_auditd_settings

Each key names an auditd.conf parameter. Enabled entries update that setting and notify one changed-only restart; package installation and boot enablement are separate. Sizes are MiB and idle time is seconds, as in auditd.conf.

Every listed entry has `enabled: false`; the table gives its `value` default.

| Entry | Default value |
| --- | --- |
| `write_logs` | `"yes"` |
| `log_file` | `"/var/log/audit/audit.log"` |
| `log_format` | `"RAW"` |
| `log_group` | `"root"` |
| `priority_boost` | `"4"` |
| `flush` | `"INCREMENTAL"` |
| `freq` | `"20"` |
| `num_logs` | `"5"` |
| `name_format` | `"NONE"` |
| `max_log_file` | `"6"` |
| `max_log_file_action` | `"keep_logs"` |
| `space_left` | `"75"` |
| `space_left_action` | `"SYSLOG"` |
| `action_mail_acct` | `"root"` |
| `admin_space_left` | `"50"` |
| `admin_space_left_action` | `"SUSPEND"` |
| `disk_full_action` | `"SUSPEND"` |
| `disk_error_action` | `"SUSPEND"` |
| `tcp_listen_queue` | `"5"` |
| `tcp_max_per_addr` | `"1"` |
| `tcp_client_max_idle` | `"0"` |
| `krb5_principal` | `"auditd"` |
| `transport` | `"TCP"` |

## ssh_hardening_server_directives

Each key is a native sshd_config directive. Only enabled entries replace that global directive. Scalar values emit one line; list values emit repeated instances, useful for Port, ListenAddress, HostKey and HostCertificate. Algorithm directives require a comma-separated scalar, not repeated lines. An empty list explicitly removes a selected global directive.

Every listed entry has `enabled: false`; the table gives its `value` default.

| Entry | Default value |
| --- | --- |
| `PermitRootLogin` | `"no"` |
| `Port` | `"22"` |
| `AddressFamily` | `"any"` |
| `ListenAddress` | `["0.0.0.0", "::"]` |
| `HostKey` | `["/etc/ssh/ssh_host_rsa_key", "/etc/ssh/ssh_host_ecdsa_key", "/etc/ssh/ssh_host_ed25519_key"]` |
| `HostCertificate` | `[]` |
| `HostKeyAlgorithms` | `"ssh-ed25519,rsa-sha2-512,rsa-sha2-256"` |
| `StrictModes` | `"yes"` |
| `SyslogFacility` | `"AUTH"` |
| `LogLevel` | `"VERBOSE"` |
| `Ciphers` | `"chacha20-poly1305@openssh.com,aes256-gcm@openssh.com,aes128-gcm@openssh.com,aes256-ctr,aes192-ctr,aes128-ctr"` |
| `MACs` | `"hmac-sha2-512-etm@openssh.com,hmac-sha2-256-etm@openssh.com,umac-128-etm@openssh.com,hmac-sha2-512,hmac-sha2-256"` |
| `KexAlgorithms` | `"sntrup761x25519-sha512@openssh.com,curve25519-sha256,curve25519-sha256@libssh.org,diffie-hellman-group-exchange-sha256"` |
| `LoginGraceTime` | `"30s"` |
| `MaxAuthTries` | `"2"` |
| `MaxSessions` | `"10"` |
| `MaxStartups` | `"10:30:60"` |
| `PubkeyAuthentication` | `"yes"` |
| `IgnoreRhosts` | `"yes"` |
| `IgnoreUserKnownHosts` | `"yes"` |
| `HostbasedAuthentication` | `"no"` |
| `UsePAM` | `"yes"` |
| `AuthenticationMethods` | `"publickey"` |
| `PasswordAuthentication` | `"no"` |
| `PermitEmptyPasswords` | `"no"` |
| `KbdInteractiveAuthentication` | `"no"` |
| `KerberosAuthentication` | `"no"` |
| `KerberosOrLocalPasswd` | `"no"` |
| `KerberosTicketCleanup` | `"yes"` |
| `GSSAPIAuthentication` | `"no"` |
| `GSSAPICleanupCredentials` | `"yes"` |
| `DenyUsers` | `""` |
| `AllowUsers` | `""` |
| `DenyGroups` | `""` |
| `AllowGroups` | `""` |
| `AuthorizedKeysFile` | `".ssh/authorized_keys"` |
| `TrustedUserCAKeys` | `"/etc/ssh/trusted-user-ca-keys"` |
| `AuthorizedPrincipalsFile` | `"/etc/ssh/auth_principals/%u"` |
| `TCPKeepAlive` | `"no"` |
| `ClientAliveInterval` | `"300"` |
| `ClientAliveCountMax` | `"3"` |
| `PermitTunnel` | `"no"` |
| `AllowTcpForwarding` | `"no"` |
| `AllowAgentForwarding` | `"no"` |
| `GatewayPorts` | `"no"` |
| `X11Forwarding` | `"no"` |
| `X11UseLocalhost` | `"yes"` |
| `PermitUserEnvironment` | `"no"` |
| `AcceptEnv` | `"LANG LC_*"` |
| `Compression` | `"no"` |
| `UseDNS` | `"no"` |
| `PrintMotd` | `"no"` |
| `PrintLastLog` | `"no"` |
| `Banner` | `"/etc/issue.net"` |
| `DebianBanner` | `"no"` |
| `RevokedKeys` | `"/etc/ssh/revoked_keys"` |
| `Subsystem` | `"sftp internal-sftp -l INFO -f LOCAL6 -u 0027"` |

Edit `roles/linux-hardening/files/ssh_banner` to customize the pre-authentication SSH message. The default enabled `Banner` directive points to `/etc/issue.net`; the role copies the file before validating SSH configuration. Setting `Banner.value: none` disables the message and skips the copy. Setting `Banner.enabled: false` leaves the existing SSH directive and banner file unchanged.

## ssh_hardening_client_directives

Each key is a native ssh_config directive. The same enabled/value schema applies; Host-specific exceptions retain precedence. Native validation rejects unsupported values.

Every listed entry has `enabled: false`; the table gives its `value` default.

| Entry | Default value |
| --- | --- |
| `AddressFamily` | `"any"` |
| `Port` | `"22"` |
| `BatchMode` | `"no"` |
| `CheckHostIP` | `"yes"` |
| `StrictHostKeyChecking` | `"ask"` |
| `Ciphers` | `"chacha20-poly1305@openssh.com,aes256-gcm@openssh.com,aes128-gcm@openssh.com,aes256-ctr,aes192-ctr,aes128-ctr"` |
| `MACs` | `"hmac-sha2-512-etm@openssh.com,hmac-sha2-256-etm@openssh.com,umac-128-etm@openssh.com,hmac-sha2-512,hmac-sha2-256"` |
| `KexAlgorithms` | `"sntrup761x25519-sha512@openssh.com,curve25519-sha256,curve25519-sha256@libssh.org,diffie-hellman-group-exchange-sha256"` |
| `HostKeyAlgorithms` | `"ssh-ed25519,rsa-sha2-512,rsa-sha2-256"` |
| `ForwardAgent` | `"no"` |
| `ForwardX11` | `"no"` |
| `HostbasedAuthentication` | `"no"` |
| `PasswordAuthentication` | `"no"` |
| `GSSAPIAuthentication` | `"no"` |
| `GSSAPIDelegateCredentials` | `"no"` |
| `Tunnel` | `"no"` |
| `PermitLocalCommand` | `"no"` |
| `Compression` | `"no"` |

## linux_hardening_modules

The map contains a separate YAML boolean for each module. Every default is false. A true value writes only that module policy, rejecting mounted filesystems and EFI-dependent vfat. The policy does not unload modules.

| Module | Default |
| --- | --- |
| `cramfs` | `false` |
| `freevxfs` | `false` |
| `jffs2` | `false` |
| `hfs` | `false` |
| `hfsplus` | `false` |
| `squashfs` | `false` |
| `udf` | `false` |
| `vfat` | `false` |
| `dccp` | `false` |
| `rds` | `false` |
| `sctp` | `false` |
| `tipc` | `false` |

## linux_hardening_mounts

Each named entry contains `enabled: false` for mount options and `permissions_enabled: false` for directory ownership/mode. `src` or `fstype` empty means discover it from the existing mount. All entries default to `owner: root`, `dump: "0"`, `passno: "0"`. The two switches are independent.

| Entry | path | src | fstype | opts | mode | group |
| --- | --- | --- | --- | --- | --- | --- |
| `proc` | `"/proc"` | `"proc"` | `"proc"` | `"rw,nosuid,nodev,noexec,relatime,hidepid=2"` | `"0555"` | `"root"` |
| `boot` | `"/boot"` | `""` | `""` | `"rw,nosuid,nodev,noexec"` | `"0700"` | `"root"` |
| `dev` | `"/dev"` | `"devtmpfs"` | `"devtmpfs"` | `"rw,nosuid,noexec"` | `"0755"` | `"root"` |
| `dev_shm` | `"/dev/shm"` | `"tmpfs"` | `"tmpfs"` | `"rw,nosuid,nodev,noexec"` | `"1777"` | `"root"` |
| `home` | `"/home"` | `""` | `""` | `"rw,nosuid,nodev"` | `"0755"` | `"root"` |
| `run` | `"/run"` | `"tmpfs"` | `"tmpfs"` | `"rw,nosuid,nodev"` | `"0755"` | `"root"` |
| `tmp` | `"/tmp"` | `""` | `""` | `"rw,nosuid,nodev,noexec"` | `"1777"` | `"root"` |
| `var` | `"/var"` | `""` | `""` | `"rw,nosuid,nodev"` | `"0755"` | `"root"` |
| `var_log` | `"/var/log"` | `""` | `""` | `"rw,nosuid,nodev,noexec"` | `"0755"` | `"{{ 'syslog' if ansible_facts.distribution == 'Ubuntu' else 'root' }}"` |
| `var_log_audit` | `"/var/log/audit"` | `""` | `""` | `"rw,nosuid,nodev,noexec"` | `"0700"` | `"root"` |
| `var_tmp` | `"/var/tmp"` | `""` | `""` | `"rw,nosuid,nodev,noexec"` | `"1777"` | `"root"` |

## ssh_hardening_server_matches and ssh_hardening_client_hosts

Both default to `[]`. Each item requires:

| Field | Default / requirement | Meaning |
| --- | --- | --- |
| `id` | Required | Stable lowercase identifier using letters, digits, `_` or `-`. |
| `enabled` | Required boolean | True permits managing this scope; false leaves it untouched. |
| `match` | Required string | Server: User, Group, Address or LocalPort criterion. Client: Host patterns. |
| `directives` | Required map | Native directive to `{enabled: boolean, value: scalar-or-list}`; each rule requires true. |

There is no enabled default for new items: explicitly provide the boolean. Changing the criterion of an existing role scope is refused. The README includes SFTP and client-host examples.

## ssh_hardening_key_files

Defaults to `[]`. CA, revocation and authorized-principal files share this interface. Contents alone never activate it.

| Field | Default / requirement | Meaning |
| --- | --- | --- |
| `enabled` | Required boolean | Only true permits file or directory changes. |
| `path` | Required absolute path | Destination public-key/principal/revocation file. |
| `lines` | Required string list | One key or principal per line; empty list explicitly clears the file. |
| `owner` | `root` | File and parent-directory owner. |
| `group` | `root` | File and parent-directory group. |
| `mode` | `'0644'` | File mode, quoted octal. Use readable principals files when sshd must read as the target user. |
| `directory_mode` | `'0755'` | Parent-directory mode, quoted octal. |

Set the corresponding SSH directive separately. Existing files managed externally can be referenced by an enabled directive without enabling a file item.

## Fixed internal paths and Ansible context

`vars/main.yml` fixes `linux_hardening_ssh_service: ssh` and `linux_hardening_nologin: /usr/sbin/nologin`. Other paths are normal Debian/Ubuntu configuration paths in tasks. They are not distribution dispatch tables or public configuration switches.

The role uses caller-supplied `ansible_facts.distribution`, `distribution_version`, and (for firewall preflight) `service_mgr`; normal `gather_facts: true` supplies these. `ansible_connection` distinguishes local from remote verification. `ansible_port` defaults to 22 for the remote firewall preflight; declare it explicitly when using another management port. `ansible_check_mode` prevents application. Registered task results are transient internal state, not user variables.

Local databases, active mounts, EFI presence, enabled SSH Includes, and selected-family firewall snapshots are inspected only by controls that need them. No remote environment variable is needed for firewall generation.
