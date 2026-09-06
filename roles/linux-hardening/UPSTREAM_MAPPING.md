# Upstream coverage and changes

Reviewed source: [dev-sec/ansible-collection-hardening, commit 3102eddbd116c5f8c1581aca543d372dbc326764](https://github.com/dev-sec/ansible-collection-hardening/tree/3102eddbd116c5f8c1581aca543d372dbc326764). The review covered both roles' tasks, defaults, main and Debian/Ubuntu variables, handlers, applicable templates, argument specifications, and SSH policy assets. This is a port of the applicable controls, not a dependency on the upstream collection.

All upstream automatic hardening defaults become explicit opt-in controls. `false` never removes or reverses a setting. Native-name settings dictionaries are individually gated; there is no value-presence activation. See [VARIABLES.md](VARIABLES.md) for the complete setting inventory and exact defaults.

## Linux role

| Upstream task/file | Disposition and replacement | Reason or retained behavior |
| --- | --- | --- |
| `main.yml`, `hardening.yml`: main enable switch and task imports | Simplified into `tasks/main.yml`, `linux.yml`, `ssh.yml`, `iptables.yml` | Individual switches replace an automatically active baseline. |
| `hardening.yml`: setup, first-found variable loading, repeated set_fact overrides | Omitted | Caller supplies facts once. Debian/Ubuntu paths and values are direct defaults/vars; no distribution search hierarchy is needed. |
| `apt.yml`: remove insecure packages | Retained, `linux_hardening_remove_insecure_packages` and package list | Debian package names replace generic server package aliases. One conditional apt operation, no cache refresh, upgrade, or autoremove. |
| `auditd.yml`: install package | Retained, `linux_hardening_auditd_install` | No install just because configuration values exist. Package-triggered start is suppressed. |
| `auditd.yml` and `auditd.conf.j2`: audit log, format, ownership, flush/frequency, rotation/retention, space thresholds/actions, disk errors, mail, priority, TCP connection limits, Kerberos principal | Retained as individually enabled `linux_hardening_auditd_settings` entries | Update only selected lines; do not replace the file or overwrite disabled settings. Restart only on an actual configuration change. |
| `auditd.conf.j2`: `dispatcher`, `disp_qos` | Omitted | Separate audispd dispatcher settings are obsolete with modern auditd's integrated dispatcher. Reintroducing a nonexistent `/sbin/audispd` can break auditing. |
| `auditd.conf.j2`: `enable_krb5` | Replaced by gated `transport` | `enable_krb5` is deprecated; `transport` is its documented replacement. The supplied value TCP matches upstream's disabled Kerberos setting and does not itself open a listener. |
| `auditd.yml`: stop/mask journald audit socket and restart journald | Retained, `linux_hardening_disable_journald_audit` | Separate from audit package installation and all audit settings. |
| `cron.yml`: find cron paths and remove group/other access | Retained, `linux_hardening_cron_permissions` | One bounded discovery followed by changes to existing paths only. |
| `ctrlaltdel.yml`: mask reboot shortcut | Retained, `linux_hardening_disable_ctrl_alt_del` | No unconditional daemon reload. |
| `limits.yml` and systemd/profile core templates: PAM limits, systemd core storage, shell soft limits | Merged into `linux_hardening_disable_core_dumps` | One coherent core-dump control; includes root's limits and disables systemd core processing as well as storage. No unnecessary systemd reload. |
| `limits.yml`: enable core dumps by deleting an entire systemd drop-in directory | Omitted | A false hardening control must not remove files, especially other owners' drop-ins. Explicitly migrate any existing policy when re-enabling dumps. |
| `login_defs.yml`, `login.defs.j2`: login logging, PATHs, tty permissions/group, umask, user groups, password ageing, UID/GID/sub-ID ranges, retries/timeout, home requirement, chfn, mail/home defaults, crypt method/rounds | Retained as individually enabled `linux_hardening_login_defs` entries | Preserve unrelated and disabled lines. File ownership/mode is separately gated by `linux_hardening_login_defs_permissions`. |
| `login.defs.j2`: force SHA512 and legacy `MD5_CRYPT_ENAB` | SHA512 replaced as the suggested `ENCRYPT_METHOD` by YESCRYPT; MD5 compatibility toggle omitted | Current Debian/Ubuntu use yescrypt. Do not downgrade a modern password hash solely to copy a legacy baseline. SHA512 and its round controls remain explicitly selectable values; existing hashes are not rewritten. |
| `login.defs.j2`: `FAILLOG_ENAB`, `FTMP_FILE` | Omitted from supplied defaults | Legacy faillog/failed-utmp controls are absent from current Debian 13 shadow documentation. PAM/faillock and audit controls are retained; there is no blanket replacement of login.defs. |
| `minimize_access.yml`: writable search-path files | Retained, `linux_hardening_minimize_path_permissions` | Safe argv-based find, no shell interpolation or ignored errors, unique resulting paths. |
| `minimize_access.yml`: shadow and passwd/group permissions, including backups | Retained as separate shadow/passwd switches | Debian shadow ownership remains root:shadow 0640; passwd/group remains root:root 0644. Missing backup files are not created. |
| `minimize_access.yml`: restrict `su` | Retained, `linux_hardening_restrict_su` | One explicit switch instead of activation by absence of a value in an allowlist. |
| `minimize_access.yml`: `/proc` hidepid and mount flags | Retained as `linux_hardening_mounts.proc.enabled` and explicit options | No mountpoint set_fact accumulation. Active source/type comes from `findmnt` only for the selected mount. |
| `minimize_access_fs.yml`: `/boot`, `/dev`, `/dev/shm`, `/home`, `/run`, `/tmp`, `/var`, `/var/log`, `/var/log/audit`, `/var/tmp` mount options and permissions | Retained as individual entries in `linux_hardening_mounts` | Mount options and directory permissions have separate switches. Only existing mounts are remounted; no guessed block devices or fabricated filesystems. Ubuntu `/var/log` group remains syslog; default 0755 is stricter than upstream Ubuntu 0775. |
| `modprobe.yml`, `modprobe.j2`: block unused filesystems and obsolete network modules | Retained as per-module booleans | Each enabled module gets its own file. Use `/bin/false` plus blacklist. Reject mounted filesystem/EFI conflicts instead of silently removing entries from the policy. Never unload modules during a run. |
| `modprobe.yml`: install kmod automatically | Omitted | Standard host prerequisite; writing a module policy does not authorize package installation. |
| `modprobe.yml`: mutate the user's filesystem list, value-based whitelist | Replaced | Each module has its own explicit boolean; false leaves any existing policy unchanged. |
| `pam.yml`: remove credential caching package | Retained, `linux_hardening_remove_pam_ccreds` | Separate from other PAM controls; no package-fact enumeration. |
| `pam.yml`: libuser SHA512 setting | Retained, `linux_hardening_libuser_hash` and value | Update one INI key instead of replacing the entire libuser configuration. Relevant only for hosts using libuser. |
| `pam_debian.yml`: passwdqc installation/configuration | Retained, `linux_hardening_pam_passwdqc` | Use the canonical Debian `passwdqc` profile, avoid duplicate profiles, enable on configuration change or detected inactive integration. |
| `pam_debian.yml`: tally2/faillock version branching | Simplified to faillock | The supported release floor has Linux-PAM >= 1.4. Legacy tally2 is removed; no package facts/version branching needed. |
| `pam_debian.yml` and `faillock.conf.j2`: retries, unlock time, root lockout | Retained as independently enabled faillock settings and a separate PAM activation switch | Root lockout is no longer an unconditional line. |
| `pam_debian.yml`: remove passwdqc/tally/faillock when a feature is false or retries is zero | Omitted | Disabled controls must not remove packages or files. Keep a control enabled to edit its value; perform explicit decommissioning separately. |
| `pam_debian.yml`: always run `pam-auth-update --package` | Replaced by named-profile handlers | Only changed profiles or detected inactive integration trigger updates; effective stack checks fail visibly if locally customized PAM files prevent activation. |
| `pam_debian.yml`: no_pass_expiry for key login | Retained, `linux_hardening_pam_no_pass_expiry` | Separate explicit switch; only edits the existing pam_unix account line. |
| `profile.yml`: core limit and logout timeout | Core limit merged above; timeout retained independently | A false flag never deletes a profile file. Added optional shell umask application to complement login.defs. |
| `securetty.yml` | Retained, `linux_hardening_securetty` | Explicit console allowlist, root:root 0400. Only effective if the installed login/PAM stack uses this file. |
| `rhosts.yml`, `netrc.yml`: enumerate accounts and remove files; hosts.equiv removal | Retained as three separate controls | One local passwd lookup is shared with account hardening. Use actual home paths, not tilde expansion; preserve the netrc user exemption list. |
| `suid_sgid.yml`: blacklist and unknown-binary removal | Retained as independent switches and lists | Stat blacklisted paths instead of swallowing every failure. Unknown scan runs only when enabled; whitelist includes merged-/usr forms. Non-Debian paths are removed. |
| `sysctl.yml`: kernel, VM, filesystem, IPv4 and IPv6 controls, plus Debian/Ubuntu user-namespace and BPF settings | All active reference entries retained in `linux_hardening_sysctl_settings` | Each key has its own switch plus the kernel master switch. Apply live value once and persist that key without repeatedly reloading the whole file. Unsupported selected keys fail visibly. |
| `sysctl.yml`: touch/chmod config on every run | Replaced by separate `linux_hardening_sysctl_permissions` | No mtime churn or permissions change unless explicitly requested. |
| `sysctl.yml`: blanket container skip and ignored unsupported entries/errors | Omitted | No silent claim that an enabled control was enforced. Host-only controls need host privileges; unsupported kernels/containers fail rather than silently bypass policy. |
| `user_accounts.yml`: root/regular/system classification and account exemptions | Retained, simplified to loop conditions on one local passwd database | No incremental set_fact lists, no LDAP/NIS enumeration, no duplicate root lookup. |
| `user_accounts.yml`: remove system shells and lock passwords | Retained as separate switches | Lock existing hashes using user module's lock operation instead of overwriting passwords with `*`. Existing password contents are preserved. |
| `user_accounts.yml`: root/regular password ageing | Retained as separate switches | Skip locked hashes, preserve ageing exemption list. Shadow data is read only when needed and hidden in output. |
| `user_accounts.yml`: root/regular home permissions | Retained as separate switches | Preserve explicit home exemption list. |
| `user_accounts.yml`: remove duplicate UID 0 accounts | Retained, `linux_hardening_remove_duplicate_root` | Never removes the account named root. |
| `selinux.yml`: policy/state | Retained for explicitly provisioned Debian/Ubuntu SELinux hosts | `linux_hardening_selinux_enabled`, policy `default`, state `enforcing`. Does not install SELinux, change boot parameters, disable AppArmor, or reboot. |
| `handlers/main.yml`: audit, journald, remount, initramfs, daemon reload | Simplified | Audit/journald only after change; mount module handles necessary remounts; initramfs refresh separately gated and notified by module changes; unnecessary daemon reload removed. |
| All task/variable/template branches exclusive to unsupported systems | Omitted | No unsupported OS package managers, authentication stacks, crypto policies, service paths, init files, distribution selectors, or handlers are shipped. |
| Upstream values without Debian/Ubuntu tasks (`os_auth_pw_remember`, oddjob/SSSD/password-quality paths, single-user init prompts) | Omitted | These are unused or belong to another platform's implementation. The Debian reference does not enforce password history through that unused variable; this port does not claim otherwise. |

## SSH role

| Upstream task/file | Disposition and replacement | Reason or retained behavior |
| --- | --- | --- |
| `main.yml`, `hardening.yml`: enabled wrappers and per-platform discovery | Simplified to direct Debian/Ubuntu values and individual gates | No automatic package installation, configuration replacement, key rotation, service start, or boot enablement. |
| `install.yml`: server/client packages | Retained as independent install switches | One apt invocation per explicitly selected component; server package starts suppressed. |
| `install.yml`, end of `hardening.yml`: repeated service enablement | Merged into `ssh_hardening_enable_service` | One idempotent start/enable operation on request. |
| `disable-systemd-socket.yml`: stop/mask socket, remove activation units, start service | Intentionally omitted | This is a listener migration, not a security control. Automatically stopping a live listener risks access loss. Authentication hardening works with the existing service; listener edits are rejected during socket activation until the operator performs a separate migration. |
| `install.yml`: unconditionally create `/run/sshd` | Omitted | Supported package/service units own this runtime directory. The role requires a functioning server for transactional configuration, avoiding recreation on every run. |
| `crypto_ciphers.yml`, `crypto_macs.yml`, `crypto_kex.yml`: historical version selection | Simplified | Retain the upstream modern cipher/MAC sets. KEX includes the hybrid sntrup761 algorithm supported across the release floor plus curve25519 and DH group-exchange SHA256. No obsolete version branches or repeated set_fact tasks. Administrators may select newer algorithms for newer homogeneous fleets. |
| `crypto_hostkeys.yml`: RSA generation and key file permissions | Retained as independent `ssh_hardening_regenerate_rsa_key` and `ssh_hardening_host_key_permissions` | Never rotate keys just because the role ran or a size value exists. |
| `opensshd.conf.j2`: all supported global directives | Retained in `ssh_hardening_server_directives` | Each individual native directive has its own switch. Includes are staged and validated. Preserve disabled global settings and existing Match scopes rather than overwriting the entire file. |
| `openssh.conf.j2`: all supported client directives and per-host options | Retained in `ssh_hardening_client_directives` and gated `ssh_hardening_client_hosts` | Includes and Host precedence retained; native `ssh -G` validation before writes. |
| `opensshd.conf.j2`: hard-coded legacy Protocol, UseLogin, UsePrivilegeSeparation | Omitted | Protocol 1 and configurable privilege separation/login legacy modes are removed in supported OpenSSH; privilege separation is mandatory. Reintroducing unsupported directives adds no protection. |
| `openssh.conf.j2`: Protocol, RSAAuthentication, RhostsRSAAuthentication, UseRoaming | Omitted | These obsolete directives are not applicable to the supported OpenSSH floor. Modern host-based authentication controls remain. |
| `opensshd.conf.j2`: ChallengeResponseAuthentication | Replaced with `KbdInteractiveAuthentication` | Canonical current directive; its deprecated alias is removed only when that control is enabled. |
| `opensshd.conf.j2`: Match User/Group/Address/LocalPort and custom raw directives | Merged into gated native directive dictionaries and per-rule scopes | No raw option list that activates simply by having values. Stable block identifiers preserve disabled rules. |
| `opensshd.conf.j2`: SFTP subsystem, umask, logging, sftponly ForceCommand, chroot, forwarding restrictions | Retained as `Subsystem` plus independently gated Match directives | README gives the complete restricted-SFTP example; group existence and chroot filesystem ownership are not implicitly changed. |
| `hardening.yml`: dynamic PAM MOTD removal | Retained, `ssh_hardening_disable_pam_motd` | No side effect from disabling an unrelated banner setting. |
| `hardening.yml`: weak DH moduli cleanup | Retained, `ssh_hardening_filter_moduli` | Atomic, idempotent Python filtering; preserve comments, interpret size field correctly, fail if no sufficiently large group remains. No shell interpolation, discarded errors, or SSH restart just to update moduli. |
| `ca_keys_and_principals.yml`, revoked key templates | Merged into per-file `ssh_hardening_key_files` plus directive gates | Root-owned public CA/revocation/principal files by default, independent file enable switches, no value-triggered creation. Auth-time file reads do not need a restart. |
| `selinux.yml`: package installation and SSH port labels | Retained as independent Debian/Ubuntu-compatible package and seport controls | Explicitly provisioned SELinux hosts only; no facts-based automatic enablement. |
| `selinux.yml`: compile/install custom `ssh_password` direct shadow-read policy | Omitted | This grants additional access to sshd when PAM is disabled, rather than hardening it. Keep PAM integration or provision and review a site-specific policy separately; the role does not add this exception. |
| `selinux.yml`: remove `ssh_password` policy when PAM is used | Retained under `ssh_hardening_selinux_remove_password_policy` | A named explicit hardening operation; inspect installed modules only when removal is requested. |
| `hardening.yml` and `files/sshd`: disable external distro crypto policy | Omitted | Not part of Debian/Ubuntu's SSH configuration; no crypto-policy or sysconfig path is introduced. |
| `handlers/main.yml`: unconditional restart on template/key-list changes | Replaced | Staged config validation, changed-only handler, live validation, reload, independent timed rollback, fresh authenticated connection, explicit commit. Key generation has its own validation/reload handler. |

The supplied defaults enumerate every applicable global directive, including root and password restrictions, public keys/PAM/authentication methods, empty passwords, login throttling, host-based/known-host trust, Kerberos/GSSAPI behavior, user/group allow/deny lists, CA/principal/revocation paths, host keys/certificates/algorithms, keepalives, tunneling, TCP/agent/X11 forwarding, gateway binding, environment acceptance, compression/DNS, banners/MOTD/lastlog, logging, listeners, and SFTP.

## Upstream UFW settings to iptables

This section names the old variables solely for traceability. No runtime task, template, package operation, handler, or module depends on UFW. Upstream only rendered its defaults; it did not install an equivalent complete host firewall through this code path.

| Upstream setting/behavior | New implementation |
| --- | --- |
| `ufw_manage_defaults` | `iptables_hardening_enabled` is the master gate. Family, policy, and individual rule gates remain necessary. |
| `ufw_default_input_policy` | `iptables_hardening_default_input_policy_enabled` plus `iptables_hardening_default_input_policy`; selected filter INPUT policy only. |
| `ufw_default_output_policy` | Separate OUTPUT gate/value. Default value ACCEPT does nothing until enabled. |
| `ufw_default_forward_policy` | Separate FORWARD gate/value. Default value DROP does nothing until enabled. |
| `ufw_enable_ipv6` | Independent `iptables_hardening_ipv4_enabled` and `iptables_hardening_ipv6_enabled`. IPv6 false leaves its existing policy untouched. |
| `ufw_ipt_sysctl` | No firewall-owned sysctl loader. Independently enabled kernel parameters are managed once by `ansible.posix.sysctl`. |
| `ufw_manage_builtins` | Only explicitly enabled built-in policies are changed. Foreign filter chains/rules and other runtime tables are preserved. |
| `ufw_default_application_policy` | Application-profile abstraction omitted. Explicit inbound/outbound TCP/UDP lists each have their own switches. |
| `ufw_ipt_modules` auto-loaded FTP/NAT/NetBIOS helpers | Omitted. Helpers are application-specific and expand protocol handling; ordinary conntrack rules use standard kernel support. Provision a necessary helper separately for the actual application. |
| Upstream policy `REJECT` as a default option | Only ACCEPT/DROP are built-in iptables policies. Generic REJECT is not a valid built-in policy; this role does not silently translate it or add an implicit reject rule. |
| Upstream defaults-file template | Replaced by explicit IPv4/IPv6 fragments, snapshot merge, restore test, staged atomic table application, independent rollback, and post-connection-test persistence. |
| Implicit stateful/loopback/application behavior of a firewall frontend | Explicit flags for established/related, loopback, SSH, ICMP, invalid states, anti-spoofing, logging, and each port-list group. No rule is enabled implicitly. |

The role adds persistence through the standard iptables-persistent/netfilter-persistent boot mechanism, without calling a service start/reload to apply newly generated rules. Existing persistent files are written only after successful runtime application and a fresh management connection.

## Source notes

The current [Debian auditd configuration manual](https://manpages.debian.org/trixie/auditd/auditd.conf.5.en.html) documents `transport` as the replacement for `enable_krb5`. The [iptables-restore manual](https://manpages.debian.org/trixie/iptables/iptables-restore.8.en.html) documents restore validation and locking. The [netfilter-persistent manual](https://manpages.debian.org/trixie/netfilter-persistent/netfilter-persistent.8.en.html) documents the boot plugin mechanism. For settings present only on a particular kernel or package build, an enabled unsupported setting fails visibly; a false setting remains untouched.
