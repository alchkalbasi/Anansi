# linux-hardening

A single opt-in role for Debian 12/13 and Ubuntu 22.04/24.04/26.04, derived from the Linux and OpenSSH roles in [dev-sec/ansible-collection-hardening at commit 3102eddbd116c5f8c1581aca543d372dbc326764](https://github.com/dev-sec/ansible-collection-hardening/tree/3102eddbd116c5f8c1581aca543d372dbc326764). Only Debian and Ubuntu are accepted. Firewall configuration uses iptables and ip6tables.

Every security switch defaults to `false`. An ordinary run with the supplied defaults performs validation and makes **zero configuration changes**. The role does not gather facts itself. Provide distribution/version facts, and service-manager facts for firewall use. Use `become: true` for enabled controls. Systemd, Python 3, and a functioning SSH service are required for server configuration transactions. Ansible connections must support `reset_connection` and `wait_for_connection`.

The role targets Ansible Core 2.19 or later. Install controller collections with:

```bash
ansible-galaxy collection install -r roles/linux-hardening/requirements.yml
```

On targets, the chosen control must have its normal OS tooling available. Package installation switches are separate for SSH, auditd, and iptables. PAM password-strength and faillock activation install their own required PAM packages. Filesystem module blocking assumes the normal Debian/Ubuntu `kmod` tooling; mount inspection uses `findmnt` from `util-linux`. Configuration-only controls fail if their prerequisite files/packages are absent instead of silently installing unrelated packages.

## Files

```text
roles/linux-hardening/
├── defaults/main.yml          # All public values and explicit switches
├── vars/main.yml              # Fixed Debian/Ubuntu paths
├── tasks/
│   ├── main.yml
│   ├── linux.yml
│   ├── core_dumps.yml
│   ├── accounts.yml
│   ├── pam.yml
│   ├── modules.yml
│   ├── mount.yml
│   ├── ssh.yml
│   ├── ssh_selinux.yml
│   ├── ssh_key_file.yml
│   ├── ssh_apply.yml
│   ├── ssh_commit.yml
│   ├── iptables.yml
│   └── iptables_commit.yml
├── templates/
│   ├── passwdqc.j2
│   ├── faillock.j2
│   ├── faillock_authfail.j2
│   ├── iptables.rules.j2
│   ├── ip6tables.rules.j2
│   └── iptables-common.rules.j2
├── handlers/main.yml
├── library/
│   ├── linux_hardening_validate.py
│   ├── linux_hardening_transaction.py
│   └── linux_hardening_moduli.py
├── meta/main.yml
├── tests/test_role.py
├── tests/noop.yml
├── requirements.yml
├── VARIABLES.md
├── UPSTREAM_MAPPING.md
├── LICENSE
├── NOTICE
└── README.md
```

The three role-local modules ship with the role and require no additional Python libraries on the target. The transaction module handles SSH Include files, iptables state merging, and an independent rollback watchdog. Standard configuration and account operations use Ansible collection modules.

## Tags

Every role task has the `linux-hardening` tag. Select a section with
`linux-hardening-linux`, `linux-hardening-ssh`, or `linux-hardening-iptables`.
Prerequisite validation runs with each section, and included tasks carry the
same tags as their section. Tags select tasks; controls still require their
explicit enablement switches.

Leave play-level tags unset and enable `gather_facts: true` so automatic fact
gathering also runs when selecting a section tag. The role already tags its
tasks; no extra tags are needed on the role entry. Adding all section tags to
a play or role makes every task inherit them, so selecting any section runs
them all.

```bash
ansible-playbook -i inventory hardening.yml --tags linux-hardening-ssh
```

## Boolean contract

Use YAML `true` or `false`, never quoted strings. Every scalar control and every nested `enabled` field is validated. Settings dictionaries use the native configuration name to avoid hundreds of redundant aliases:

```yaml
linux_hardening_kernel_parameters: true
linux_hardening_sysctl_settings:
  kernel.kptr_restrict:
    enabled: true
    value: '2'
  net.ipv4.ip_forward:
    enabled: false
    value: '0'

ssh_hardening_server_directives:
  PermitRootLogin:
    enabled: true
    value: 'no'
  PasswordAuthentication:
    enabled: false
    value: 'no'
```

This changes `kernel.kptr_restrict` and `PermitRootLogin`. It leaves forwarding and password authentication untouched. Sysctl entries require both the kernel-parameters switch and their own `enabled: true`. Other setting dictionaries require their per-entry switch. Firewall rules additionally require the firewall master switch and the corresponding address-family switch.

**False means unmanaged, not reverted.** If a rule was previously enabled, changing its switch to false preserves its existing configuration and runtime effect. Automatically deleting it would violate the no-change requirement. To change an existing setting, keep it enabled and choose a new value. To remove an explicitly managed SSH directive, use `enabled: true, value: []`; matching directives in existing Match scopes are independent. To remove a managed custom firewall port group, keep that group's switch true and set its list to `[]`. Disabling the firewall master switch leaves existing runtime rules, saved rules, and service state alone, including previously enabled boot persistence.

Ansible replaces dictionaries by default. An inventory override may contain only the entries you want to manage, but each supplied entry must contain both `enabled` and `value`. There is no requirement to copy the entire defaults file. [VARIABLES.md](VARIABLES.md) documents every supplied variable and default.

## Example deployment

Use a dedicated play with serial rollout and a tested, non-root key-based management account. The role does not add authorized keys or sudo privileges for you. Keep recovery-console access available for account, PAM, filesystem, and kernel changes.

```yaml
---
- name: Harden selected servers
  hosts: linux_servers
  become: true
  gather_facts: true
  serial: 1
  roles:
    - role: linux-hardening
      vars:
        linux_hardening_disable_core_dumps: true
        linux_hardening_shadow_permissions: true
        linux_hardening_passwd_permissions: true
        linux_hardening_cron_permissions: true
        linux_hardening_kernel_parameters: true
        linux_hardening_sysctl_settings:
          fs.protected_hardlinks: {enabled: true, value: '1'}
          fs.protected_symlinks: {enabled: true, value: '1'}
          kernel.kptr_restrict: {enabled: true, value: '2'}
        ssh_hardening_server_directives:
          PermitRootLogin: {enabled: true, value: 'no'}
          PasswordAuthentication: {enabled: true, value: 'no'}
          KbdInteractiveAuthentication: {enabled: true, value: 'no'}
          PubkeyAuthentication: {enabled: true, value: 'yes'}
          StrictModes: {enabled: true, value: 'yes'}
          MaxAuthTries: {enabled: true, value: '2'}
          X11Forwarding: {enabled: true, value: 'no'}
        iptables_hardening_enabled: true
        iptables_hardening_install_packages: true
        iptables_hardening_persistent: true
        iptables_hardening_ipv4_enabled: true
        iptables_hardening_ipv6_enabled: true
        iptables_hardening_default_input_policy_enabled: true
        iptables_hardening_default_input_policy: DROP
        iptables_hardening_default_forward_policy_enabled: true
        iptables_hardening_default_forward_policy: DROP
        iptables_hardening_default_output_policy_enabled: false
        iptables_hardening_allow_loopback: true
        iptables_hardening_allow_established: true
        iptables_hardening_allow_ssh: true
        iptables_hardening_ssh_port: 22
        iptables_hardening_allow_icmp: true
        iptables_hardening_drop_invalid: true
        iptables_hardening_anti_spoofing: true
        iptables_hardening_allow_custom_tcp_ports: true
        iptables_hardening_tcp_ports: [80, 443]
```

Set `ansible_port` explicitly in the inventory to the existing management port. Start with a small set of controls; the example is not a universal policy for routers, container hosts, desktops, or application servers. A default FORWARD DROP policy and disabled kernel forwarding can disrupt routed workloads. OUTPUT DROP requires explicit outbound allowances, commonly DNS TCP/UDP 53, package repositories TCP 80/443, time synchronization UDP 123, and application-specific traffic. Existing return traffic requires `iptables_hardening_allow_established: true`.

## SSH behavior

Enabled global directives replace only the corresponding global directives, including those in local Include files. Unselected global directives, comments, and existing Match sections are preserved. The role does not replace the entire SSH configuration with a baseline. Client Host exceptions retain precedence over client-wide defaults. Existing server Match exceptions remain effective: use explicitly enabled Match controls if these should also be hardened.

```yaml
ssh_hardening_server_matches:
  - id: restricted_sftp
    enabled: true
    match: Group sftponly
    directives:
      ForceCommand: {enabled: true, value: 'internal-sftp -l INFO -f LOCAL6 -u 0027'}
      ChrootDirectory: {enabled: true, value: '/home/%u'}
      AllowTcpForwarding: {enabled: true, value: 'no'}
      AllowAgentForwarding: {enabled: true, value: 'no'}
      PermitRootLogin: {enabled: true, value: 'no'}
      X11Forwarding: {enabled: true, value: 'no'}
ssh_hardening_client_hosts:
  - id: backup
    enabled: true
    match: backup.example.net
    directives:
      Port: {enabled: true, value: '2222'}
```

A scope's stable `id` identifies its block. `enabled` on the scope and on each directive must both be true. Server criteria support User, Group, Address, and LocalPort. Changing the criterion of an existing managed scope is rejected because it would also move disabled rules to a new scope. Chroot directories must already satisfy OpenSSH's root-ownership and non-writability requirements; a user's normal writable home is not automatically a usable chroot.

CA keys, revoked keys, and authorized-principal contents share a gated file interface:

```yaml
ssh_hardening_key_files:
  - enabled: true
    path: /etc/ssh/trusted-user-ca-keys
    lines: ['ssh-ed25519 AAAA... trusted-ca']
    mode: '0644'
  - enabled: true
    path: /etc/ssh/auth_principals/deploy
    lines: ['deploy-production']
    mode: '0644'
ssh_hardening_server_directives:
  TrustedUserCAKeys: {enabled: true, value: /etc/ssh/trusted-user-ca-keys}
  AuthorizedPrincipalsFile: {enabled: true, value: '/etc/ssh/auth_principals/%u'}
```

Public-key files are read on authentication and do not require SSH reloads. Their contents, host-key regeneration, permissions, moduli filtering, and PAM changes have their own switches; they are not covered by configuration rollback. Changing an RSA host key can require updating known-host trust on clients. Disabling password authentication does not by itself disable keyboard-interactive PAM authentication; enable its separate directive when that is the intended policy.

Changed server configuration is validated as a staged Include tree with `sshd -t`. A handler applies all changed files, validates the live tree, and reloads `ssh.service` once. A transient systemd timer restores the saved configuration and reloads SSH if a new authenticated Ansible connection cannot be established and committed in time. Invalid candidates never replace live configuration. Unchanged SSH configuration does not reload the service. Client configuration is checked with `ssh -G` and never reloads a service.

Include paths must remain within `/etc/ssh`. Symlinked, repeated, or recursive configuration files are rejected instead of guessing at ownership or parse scope. Put selected exception scopes in the main configuration; earlier matching exceptions from Include files can still take precedence. Review effective Match behavior with `sshd -T -C user=...,host=...,addr=...,lport=...` for your access policies.

The role preserves socket activation. Listener changes (`Port`, `ListenAddress`, `AddressFamily`) are refused while `ssh.socket` is active. Migrate socket activation separately with console access; the role does not stop the active management listener. After applying a changed server configuration, the transaction selects the first enabled `Port` value for its fresh Ansible connection, resets the cached connection, and only then commits. Keep the current inventory port for the initial migration run; after a successful commit, update `ansible_port` in inventory to the new port so later runs can connect. On systems already using service activation, migrate ports in stages: allow old and new listening ports, add a firewall allowance for the new port, verify it, update inventory, then remove the old port while keeping its controlling setting enabled.

## Firewall behavior and persistence

The templates generate only enabled rule groups. The transaction module reads the existing filter table, replaces rules belonging to enabled groups, and preserves unrelated chains, rules, and disabled groups. Enabled built-in policy controls change only their selected policies. Role rules carry comments starting with `linux-hardening:`; reserve this prefix for this role.

There is no initial flush command. Both families are built and tested with `iptables-restore --test` / `ip6tables-restore --test` before either is applied. Each table is installed using the corresponding restore command with the xtables lock. IPv4 and IPv6 cannot commit as one kernel transaction; both have snapshots and share a rollback deadline. Runtime NAT, mangle, raw, and security tables are not rewritten. Filter counters can reset on restore.

Explicit invalid-state and anti-spoofing drops precede loopback, established/related, SSH, ICMP, and custom service allowances. Unrelated existing rules follow; rate-limited fallthrough logging is last and is emitted only for chains with an effective DROP policy. Existing ACCEPT rules can still allow traffic beyond a configured default DROP policy: review foreign rules before claiming a complete allowlist. The role deliberately does not delete another manager's rules.

Anti-spoofing blocks off-loopback loopback sources and multicast source addresses. It does not blanket-drop private networks, which could block legitimate management. ICMP allows all IPv4 ICMP or IPv6 ICMP in INPUT and OUTPUT, including error reporting, IPv6 neighbor discovery, and path MTU discovery. Restrictive IPv6 INPUT/OUTPUT policies require the ICMP flag to be explicitly true. It is not implicitly enabled. IPv6 being disabled in this role means its existing firewall remains unchanged; it does not disable IPv6 networking.

For remote application, SSH and established/related allowances must both be explicitly enabled and the SSH port must match inventory. A reset and authenticated connection test precede commit. A failed test leaves the independent rollback timer armed. A local connection test cannot prove remote accessibility; validate remote access independently when deploying with `connection: local`. Rollback reduces lockout risk but does not protect against host crashes, unavailable systemd, unrelated concurrent policy writers, or reachability changes outside the host.

`iptables_hardening_persistent: true` saves the **successfully confirmed** complete current iptables state for selected families to `/etc/iptables/rules.v4` and/or `rules.v6`, root-owned mode `0600`. Full snapshots retain other tables for boot restoration. Persistent file writes are journaled for rollback on commit failure. Only selected address families are saved. Installation disables the package's automatic save prompts and suppresses package-triggered service starts. The role enables `netfilter-persistent` for boot after commit without restarting or reloading it. Existing files for unselected families are untouched; an already configured persistence plugin may still restore those existing files at boot.

Use one firewall writer during the run. The role checks for concurrent changes before apply and commit, but shell-level snapshots cannot provide a cross-process lock against every Docker, orchestration, or firewall manager. A watchdog restores its prior snapshot; do not run competing firewall transactions during its verification window. Native iptables and the iptables compatibility interface backed by nftables are both supported. The interface and files remain iptables-oriented.

## Recovery and compatibility

Pending state is root-only under `/run/linux-hardening-server` or `/run/linux-hardening-firewall`. Successful commit cancels the timer and removes state. A rollback intentionally leaves its journal and a `rolled-back` result for inspection and refuses another run. From a recovery console, inspect `state.json` and `rolled-back`, confirm the corresponding `linux-hardening-<token>.timer` has finished, verify restored SSH/firewall state, then remove that **specific** state directory before retrying. Never delete a pending journal or stop an armed timer without checking its ownership and current state.

Linux account, PAM, sysctl, mount, and permission operations are ordinary gated Ansible operations, not an all-role rollback transaction. Account locking, ageing, root-login restrictions, hidepid, noexec, and credential policy changes need workload-specific review. Faillock can affect sudo and console authentication too. `kernel.kexec_load_disabled=1` cannot be reversed without reboot; address randomization limits depend on the architecture. Disabling user namespaces can break sandboxed applications. Some optional sysctl keys may be absent on a particular kernel: enabled unsupported keys fail visibly instead of being silently ignored. Do not blindly enable every default entry.

Module blocking never unloads a running module. It rejects currently mounted filesystems and EFI-dependent vfat. Snap-backed applications can require squashfs even when their mounts are not visible in the current namespace. Refreshing initramfs is a separate explicit flag and runs only when module configuration changes. Existing mounts are hardened only when requested; the role refuses an unmounted path rather than fabricating a new filesystem or fstab source. Directory permissions are separately gated.

`/etc/securetty` is effective only where the PAM/login stack consumes it. SSH console access is controlled separately. Modern password hashing defaults to YESCRYPT for `login.defs`; explicitly selectable SHA round values preserve upstream compatibility for installations that intentionally use SHA512. Existing password hashes are not rewritten. Several historical login/audit parameters vary by package release; use the applicability notes in [UPSTREAM_MAPPING.md](UPSTREAM_MAPPING.md).

Optional SELinux mode and SSH-port labeling are retained for hosts where SELinux is already provisioned. Their explicit switches do not install a base policy, alter the boot security module, or disable AppArmor. The legacy direct shadow-read exception for sshd is not installed; its explicit removal control is available.

## Validation

```bash
python3 roles/linux-hardening/tests/test_role.py
ANSIBLE_ROLES_PATH=roles ansible-playbook -i localhost, roles/linux-hardening/tests/noop.yml --syntax-check
ANSIBLE_ROLES_PATH=roles ansible-playbook -i localhost, roles/linux-hardening/tests/noop.yml
ansible-lint --offline roles/linux-hardening
```

The Python test environment needs Ansible, PyYAML, Jinja2, and OpenSSH binaries. Tests use temporary configuration and key files; they do not change host firewall or SSH service state. Check mode validates existing prerequisite files and commands, so an enabled configuration control may fail if its package would only be installed during that check-mode run.

Validated in this checkout: 24 passing Python tests, offline role lint and syntax, all-defaults local execution with zero changes, isolated merge/rollback tests, and native OpenSSH candidate/client configuration checks on Debian 13. Live kernel firewall application, reboot persistence, real connection-loss rollback, and VM convergence across all target releases still require a disposable VM test matrix. These checks do not certify a security baseline or guarantee compatibility with every application.

[UPSTREAM_MAPPING.md](UPSTREAM_MAPPING.md) records retained controls, simplifications, replacements, and every intentionally omitted upstream task category. The Apache-2.0 license and upstream attribution are included.
