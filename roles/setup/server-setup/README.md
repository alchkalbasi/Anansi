# Server setup

Provision Debian 12+ and Ubuntu 22.04+ servers before applying
[`linux-hardening`](../../linux-hardening/README.md). The role replaces the
non-hardening steps in `server-setup.sh` with native,
idempotent Ansible tasks. Public configuration is in [defaults/main.yml](defaults/main.yml).

The default run installs a small administration package set, enables cron,
sets UTC, enables systemd-timesyncd and stores persistent journals with disk
and retention limits. The default administrator is `debian`, configured by
`server_setup_username`. Its home and `.ssh` directory are created, with
passwordless sudo access. Override `server_setup_users` for multiple accounts
or set it to `[]` to skip account provisioning. Package upgrades, automatic
updates and reboots are optional. Docker installation belongs in the separate
`docker` role.

## Requirements and running

Use Ansible Core 2.19+, systemd, Python 3 on the target and working SSH/become
access. This role cannot establish its own initial SSH connection or install
Python before Ansible connects. Start from an image with Python and sudo, or
connect as root for the initial setup. Supply `--ask-become-pass` when needed.

```sh
ansible-galaxy collection install -r roles/setup/server-setup/requirements.yml
ansible-playbook -i inventory.ini playbook.yml --tags server-setup --limit my-server --check --diff
ansible-playbook -i inventory.ini playbook.yml --tags server-setup --limit my-server
```

The root `playbook.yml` includes the role before Linux hardening; use
`--tags server-setup` to select setup there.

Example inventory:

```ini
[linux_servers]
my-server ansible_host=192.0.2.10 ansible_user=debian
```

Example group vars:

```yaml
server_setup_username: debian
server_setup_users:
  - name: "{{ server_setup_username }}"
    authorized_keys:
      - 'ssh-ed25519 AAAA... your-real-public-key'
    sudo: true
    passwordless_sudo: true
    workspace: true
server_setup_extra_packages: [net-tools, python3-pip]
```

Use real public keys. New accounts have locked passwords unless a password hash
is explicitly supplied. Password-authenticated sudo requires an existing usable
password; a new automation account normally needs an explicit passwordless sudo
grant. A supplied hash is applied only at account creation. Store it with Ansible
Vault. Existing users keep their home, shell and supplementary groups unless
explicitly configured; keys are added without removing existing keys. Workspace
ownership uses the account's actual home and primary group ID, default mode `0750`.

Every configured user gets a `.ssh` directory owned by that user with mode `0700`,
even when no public keys are supplied.

User options: `name`, `home`, `shell`, `groups`, `password`, `authorized_keys`,
`sudo`, `passwordless_sudo`, `workspace`, `workspace_path`, `workspace_mode`.
`groups` appends membership. Sudo grants are validated with `visudo` and installed
as root-owned `0440` files. This role does not remove legacy sudo grants or keys.

## Script migration

| Script step | Ansible owner |
| --- | --- |
| APT mirrors, updates, backports, proposed updates | `server_setup_apt_*`; only explicitly listed old files are disabled |
| Package installation and upgrade | `server_setup_packages`, `server_setup_extra_packages`, `server_setup_upgrade_packages` |
| Passwordless sudo | Per-user `sudo: true` and `passwordless_sudo: true` |
| Public keys | Per-user `authorized_keys` |
| SSH daemon hardening | Existing `linux-hardening`, `ssh_hardening_*` |
| iptables and boot persistence | Existing `linux-hardening`, `iptables_hardening_*` |
| Disable IPv6 | Existing `linux_hardening_kernel_parameters` and selected `linux_hardening_sysctl_settings` |
| Workspace | Per-user `workspace`, optional path and mode |

The web packages from the script (`nginx`, `certbot`, `python3-certbot-nginx`),
`net-tools` and `python3-pip` can be added with `server_setup_extra_packages`;
they are not needed on every server. iptables-persistent belongs to the hardening
role so installation does not save an unintended firewall snapshot.

[examples/bootstrap.yml](examples/bootstrap.yml) combines the script's package
profile, setup and hardening. Run from the repository root with
`ANSIBLE_ROLES_PATH="$PWD/roles" ansible-playbook -i inventory.ini roles/setup/server-setup/examples/bootstrap.yml`.
It expects an already tested `debian` key-based management account. For a fresh
root connection, run setup alone, test the new account's SSH and sudo access,
then run hardening using that account. Hardening rechecks the current connection;
a root connection cannot survive `PermitRootLogin: no`.

The current hardening defaults actively manage SSH, PAM, accounts, modules,
sysctl and firewall settings. Review them before using the combined example.
The enabled SUID blacklist includes `/usr/bin/sudo`; its task removes privilege
bits and can break non-root sudo/become access. The combined example disables
that blacklist control. On a previously hardened host, disabling the control
does not restore removed privilege bits; repair sudo through an already privileged
session before switching to a non-root management account.
Keep `UsePAM: yes` on Debian/Ubuntu instead of copying the script's `no`.

IPv6 remains enabled. The combined example enables IPv6 firewall controls. To
disable it intentionally, override the combined example's hardening sysctl entries for
`net.ipv6.conf.all.disable_ipv6`, `net.ipv6.conf.default.disable_ipv6` and
`net.ipv6.conf.lo.disable_ipv6`, each with `enabled: true, value: '1'` and the
parent `linux_hardening_kernel_parameters: true`. Also review SSH's IPv6 listen
addresses before disabling IPv6.

## Mirrors and updates

OS source management is enabled by default (`server_setup_manage_apt_sources: true`).
Set it to `false` to leave OS sources unmanaged. When enabled, the role writes signed deb822 sources to
`/etc/apt/sources.list.d/server-setup.sources` using the detected release.
Normal updates and security repositories are included. Backports and proposed
updates each require a separate switch. Set `server_setup_apt_source_packages: true`
to include `deb-src` alongside binary packages in both OS stanzas.
Default mirrors use distribution archive
keys; custom mirrors must serve packages signed by the same trusted archive keys.
Ubuntu ARM and other ports architectures need an appropriate Ubuntu ports mirror.

To replace the old script's Debian mirror:

```yaml
server_setup_manage_apt_sources: true
server_setup_apt_mirror: https://repo.mizbaninternal.ir/repository/debian/
server_setup_apt_security_mirror: https://repo.mizbaninternal.ir/repository/debian-security/
server_setup_apt_sources_to_disable:
  - /etc/apt/sources.list
  - /etc/apt/sources.list.d/debian.sources
  - /etc/apt/sources.list.d/mizban_repo.list
```

List only files that exist or are known obsolete; missing files are skipped.
Explicitly selected files are renamed to `.server-setup-disabled`, retaining their
contents. No other source files are disabled. For rollback, restore those files
and explicitly remove the role's managed source file. The role never deletes unknown repos.
APT refreshes immediately after source changes; other refreshes use a one-hour
cache. Package installations fail rather than silently remove existing packages.

### Downloaded keys and additional repositories

The script's `docker-install.sh` downloads `GPG_URL` and writes a repository
entry using `signed-by`. Configure the same pattern here with
`server_setup_apt_repositories` (empty by default), independently of OS source
management. For the internal Docker mirror from the script:

```yaml
server_setup_apt_repositories:
  - name: docker
    url: https://repo.mizbaninternal.ir/repository/debian-docker/
    key_url: https://repo.mizbaninternal.ir/repository/debian-docker/gpg
    key_format: asc
    suites: ["{{ ansible_facts.distribution_release }}"]
    components: [stable]
    architectures: [amd64]  # Set the actual APT architecture, e.g. arm64.
    # key_checksum: sha256:YOUR_VERIFIED_KEY_CHECKSUM
```

For mirrors signed with an already installed archive key, use
`signed_by: /usr/share/keyrings/debian-archive-keyring.gpg` instead of `key_url`.
Specify exactly one of these options. The existing keyring must be readable by APT;
the role does not download or replace it.

The role installs `ca-certificates`, downloads each configured `key_url` over verified HTTPS to
`/etc/apt/keyrings/server-setup-NAME.asc`, then writes
`/etc/apt/sources.list.d/server-setup-NAME.sources` referencing that key through
`Signed-By`. Keys are root-owned and readable by APT (`0644`). Use `key_format: gpg`
only when the URL serves a binary OpenPGP keyring; ASCII-armored keys use `asc`
(the default). No conversion or global `apt-key` trust is used. Optional
`key_checksum` accepts the Ansible `get_url` checksum syntax. Key or source changes
force a package-index refresh before base/extra package installation.

This configures the repository only; Docker installation remains in the `docker`
role. Have one role own each repository to avoid duplicate entries. Removing an
entry leaves its existing key and source unmanaged; remove them explicitly when
retiring a repository. Check mode does not download or validate key contents.
See [APT signing-key guidance](https://manpages.debian.org/testing/apt/apt-secure.8.en.html)
and [Ansible get_url](https://docs.ansible.com/projects/ansible-core/devel/collections/ansible/builtin/get_url_module.html).

`server_setup_upgrade_packages: true` runs a safe upgrade, preserving local
configuration and preventing package removals. `server_setup_allow_reboot: true`
is a separate authorization, valid only alongside upgrades. Reboots occur only
when the upgrade phase ran and `/var/run/reboot-required` exists. Some Debian
packages do not create this marker: its absence does not prove no reboot is needed.
Upgrade maintenance remains an operator responsibility.

`server_setup_unattended_upgrades_enabled: true` enables the distribution's
unattended-upgrades policy and APT timers, with automatic reboots explicitly off.
Review `/etc/apt/apt.conf.d/50unattended-upgrades` and run
`unattended-upgrade --dry-run --debug` before relying on custom mirror coverage.
Existing origin overrides remain in effect. Keep this disabled when updates
are managed through maintenance windows elsewhere.

## Host services

The role templates `/etc/resolv.conf` before package operations, owned by
`root:root` with mode `0644`, on supported Debian and Ubuntu hosts. Existing
symlinks are followed. Nameservers default to `8.8.8.8` and `1.1.1.1`; search
domains and resolver options default to empty lists. Override them in inventory
host/group vars as needed:

```yaml
server_setup_resolv_nameservers: [8.8.8.8, 1.1.1.1]
server_setup_resolv_search: [example.internal]
server_setup_resolv_options: [timeout:2, attempts:3]
```

At least one nameserver is required. Set `server_setup_manage_resolv_conf: false`
to leave the resolver unmanaged. DHCP, NetworkManager or systemd-resolved can
rewrite this file later; configure their DNS settings separately when applicable.

Time sync uses systemd-timesyncd. Set `server_setup_ntp_servers` for internal
servers. If chrony/ntpd already owns time synchronization, set
`server_setup_time_sync_enabled: false`; the role will not remove a competing
provider. `server_setup_timezone: ''` leaves timezone unmanaged. Persistent
journals use `512M` maximum, `1G` free-space reserve and one-month retention,
all configurable. Changes restart journald and flush runtime logs to disk.
Distribution logrotate policy handles file logs; cron is enabled for scheduled jobs.

Disabled switches leave previous state unmanaged; they do not uninstall packages,
remove grants, reverse configuration or stop already enabled timers/services.
Backups, remote logging, monitoring agents and application deployment depend on
your environment and belong in their existing dedicated roles.

## Tags and validation

Tags: `server-setup`, `server-setup-apt`, `server-setup-users`,
`server-setup-system`. Every section includes prerequisite
validation. Run the complete role first; isolated sections assume base packages
are present. Fact gathering works with section tags because plays have no tags.

Check mode cannot fully simulate newly created users; home-dependent tasks are
skipped when the account does not exist yet. No controller test is a live deployment result.

```sh
ANSIBLE_ROLES_PATH="$PWD/roles" ANSIBLE_LOCAL_TEMP=/tmp/anansi-ansible ansible-playbook -i localhost, roles/setup/server-setup/tests/test.yml --syntax-check
/home/ali/.local/share/pipx/venvs/ansible/bin/python roles/setup/server-setup/tests/test_role.py
```

Implementation reference: [Ansible APT module](https://docs.ansible.com/projects/ansible/latest/collections/ansible/builtin/apt_module.html).
