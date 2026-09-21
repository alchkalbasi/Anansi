# Proxmox hardening

Opt-in Ansible role for a **standalone Proxmox VE 9.x / Debian 13 amd64 host**,
including the requested PVE 9.2 on an HPE Gen10 server without Ceph. The role
checks the installed version and refuses a host with `corosync.conf`. It does
not install or upgrade Proxmox. No live PVE host was available during development.

Based on HomeSecExplorer's *Proxmox VE 9.x Hardening Guide*, version 0.9.2,
2026-02-09, supplied as `pve9-hardening-guide.md`. See [NOTICE](NOTICE) for
attribution. This implements selected controls, not the entire CIS benchmark
or a claim of CIS compliance. [CONTROLS.md](CONTROLS.md) accounts for the guide's
remaining controls and corrections.

## Run

Use the dedicated repository-root `proxmox-hardening.yml`, **not** the general
`playbook.yml`: the latter also applies `linux-hardening` to `all`, whose current
defaults enable generic controls. This role does not execute that role; only its
transaction module is shared for SSH changes.

1. Copy [examples/hosts.yml](examples/hosts.yml) into your own inventory and set
   the management IP and SSH key. Verify a separate iLO console session works.
2. Copy [examples/standalone.yml](examples/standalone.yml) to a private variables
   file. Review each enabled setting. Enable Debian `non-free-firmware` in the
   existing repositories before selecting microcode; the role does not replace
   subscription or Debian repository definitions.
3. From the repository root, collect observations first:

   ```sh
   ansible-playbook -i inventory-pve.yml proxmox-hardening.yml \
     --tags proxmox-hardening-report -e pve_hardening_report=true --limit pve-g10
   ```

4. Review and apply the selected profile:

   ```sh
   ansible-playbook -i inventory-pve.yml proxmox-hardening.yml \
     -e @pve-settings.yml --check --diff --limit pve-g10
   ansible-playbook -i inventory-pve.yml proxmox-hardening.yml \
     -e @pve-settings.yml --limit pve-g10
   ```

The current defaults enable security updates, microcode, stopping new KSM merges,
persistent journaling, audit and reporting. SSH hardening, Fail2Ban, remote logging
and backups default to `false`. Review defaults and your variable overrides before running.
`false` means **unmanaged**, not removal of a previously applied setting. Timers
and services previously enabled keep running until explicitly disabled.
String values such as `"false"` are rejected. Facts and preflight checks run
with every section tag. All tasks carry tags as their final key.

Check mode still reads real host facts/version and validates inputs. It cannot
simulate newly installed packages/services or directories; on a fresh host,
dependent tasks can fail because their prerequisites only hypothetically exist.
It never tests actual backup authentication, delivery, restore, or ban behavior.

## Controls and tags

Each tag is prefixed by `proxmox-hardening-`; `proxmox-hardening` selects all.

| Suffix | Enable variable (`pve_hardening_…`) | Behavior |
| --- | --- | --- |
| `sshd` | `sshd` | Key-only global SSH policy, validated configuration, timed rollback and fresh connection verification |
| `updates` | `security_updates` | Debian security origin only; no reboot, autoremove, or automatic PVE/kernel upgrades |
| `microcode` | `microcode` | Latest CPU-vendor microcode from existing repositories; reports need for maintenance reboot |
| `ksm` | `disable_ksm` | Stop/mask installed KSM controllers, persist `run=0`; optional immediate unmerge |
| `fail2ban` | `fail2ban` | Journal-backed GUI authentication jail, port 8006, nftables ban action |
| `logging` | `journald`, `remote_logging` | Bounded persistent journal and optional TLS rsyslog forwarding |
| `audit` | `audit` | Persistent local `/etc/pve` write/attribute watch |
| `backup` | `backup` | Encrypted configuration backup service and timer for an existing PBS |
| `report` | `report` | Read-only SSH, firewall, storage, boot and service observations |

### SSH server

Enable `pve_hardening_sshd: true` after testing administrator SSH keys in a new
session and independent iLO console access. Run just this control with:

```sh
ansible-playbook -i inventories/production/hosts.yml proxmox-hardening.yml \
  --tags proxmox-hardening-sshd -e pve_hardening_sshd=true --limit <node>
```

The global policy allows root with keys (`PermitRootLogin prohibit-password`),
requires public-key authentication, disables password, keyboard-interactive and
empty-password login, enables strict permission checks and PAM account/session
handling, disables X11 forwarding, and sets MaxAuthTries=6 and LoginGraceTime=60.
Do not select this policy if SSH keyboard-interactive/PAM MFA is required.
PVE GUI authentication and console passwords are not changed.

Existing port/listen settings, TCP forwarding, cryptographic defaults, SSH client
configuration and PVE-managed keys/symlinks are preserved. Existing `Match`
exceptions are also preserved: review `sshd -T -C user=<admin>,host=<client-name>,addr=<client-IP>`
for each required access path; the global policy does not override those exceptions.

The role shares the repository's SSH transaction module through a relative
library symlink; it does not execute the generic linux-hardening role. Keep both
role directories when copying this role. The module stages and validates the
complete configuration with `sshd -t`, handles local Include precedence, reloads
`ssh.service`, and arms an independent systemd rollback timer before writing.
A fresh native Ansible SSH connection must succeed before commit. Default
rollback is 180 seconds, connection verification 60 seconds; configure these with
`pve_hardening_sshd_rollback_seconds` and `pve_hardening_sshd_connection_timeout`.
Check mode validates the candidate without writing, reloading or reconnecting.

On connection failure, wait for rollback and inspect `/run/linux-hardening-server`
and its systemd timer from iLO. Never remove pending transaction state or stop its
watchdog. A rolled-back journal requires inspection before a retry. Avoid running
another SSH configuration manager concurrently. Setting the switch back to false
leaves previously applied settings in place.

### Updates and KSM

Security updates start on the APT timers, not as a distribution upgrade in this
play. Existing unattended-upgrade origins are intentionally replaced by this
role's late APT fragment. Kernel/PVE packages remain a separate maintenance
responsibility. Debian security package updates can still restart services.
Review effective settings with `apt-config dump` and
`unattended-upgrade --dry-run --debug`, including any locally supplied later files.

The default KSM stop mode `0` stops further merging but leaves existing shared
pages in place. For immediate unmerge set `pve_hardening_ksm_stop_mode: 2` and
`pve_hardening_ksm_unmerge_confirmed: true` only after checking available RAM.
Unmerging can exhaust memory. Existing VM definitions are not rewritten;
review their Allow KSM flags separately. Neither mode reboots the host.

### Fail2Ban and logging

Set `pve_hardening_trusted_networks` to your actual administrator/VPN addresses
before enabling the GUI jail. Invalid IP/CIDR entries and `/0` exemptions fail
preflight. The GUI jail does not add an SSH jail; SSH authentication is controlled separately by `sshd`.
It uses Fail2Ban's own nftables table, without switching the PVE firewall backend
or enabling the generic `nftables.service`. Verify a test ban on the actual
backend. For reverse-proxy access verify that PVE logs contain the real client
IP; otherwise configure the trust boundary before enabling bans.

For remote logging, provide `pve_hardening_log_server`,
`pve_hardening_log_peer` (certificate DNS name), and an existing CA trust file
in `pve_hardening_log_ca_file`. Port defaults to 6514. The collector must accept
server-authenticated TLS; mutual TLS is not implemented by this role.
Debian's standard rsyslog system-log inputs must remain enabled. The role adds
an `imfile` input for `/var/log/pveproxy/access.log`; inspect existing `imfile`
configuration for duplicate loads/inputs before enabling it. Arbitrary PVE
task-history files are not tailed recursively. The disk-assisted forwarding
queue is limited to 256 MiB, so it is not a guarantee of lossless delivery.

Audit rules are not made immutable. Existing immutable (`-e 2`) rules require
a planned reboot/change window before loading additional rules. A pmxcfs watch
must be tested on the target kernel/FUSE combination: confirm a benign change
through PVE's API creates an event with `ausearch -k pve-config`. Merely loading
the watch does not prove coverage of every change or API identity attribution.

### Encrypted configuration backups

Provision a PBS datastore and a dedicated token with the necessary
`Datastore.Backup` permissions on both the user and privilege-separated token.
Set these variables in an Ansible Vault file:

```yaml
pve_hardening_backup: true
pve_hardening_pbs_repository: 'hostbackup@pbs!g10@pbs.example.com:hosts'
pve_hardening_pbs_password: 'VAULTED_TOKEN_SECRET'
pve_hardening_pbs_key: 'VAULTED_EXISTING_PBS_KEY_JSON'
pve_hardening_pbs_key_password: 'VAULTED_KEY_PASSPHRASE'
pve_hardening_pbs_key_escrowed: true
# Set only for a certificate not validated by the host CA store:
pve_hardening_pbs_fingerprint: ''
```

Generate the client encryption key with PBS tooling, escrow the key and its
passphrase offline, then supply its JSON contents. The role never generates a
replacement key on rerun. Credential writes use `no_log`, no diff and no backup
copies, under `/root/.config/anansi-pve-backup` with mode 0700/0600. They are
outside the selected archive trees. Passphrases are read from protected files,
not command arguments. Rotate keys only with a recovery plan for older backups.

The daily timer (06:00 local by default, up to 5 minutes random delay) uploads:

| Archive | Source |
| --- | --- |
| `etc.pxar` | `/etc`, excluding nested mounts by PBS default |
| `pve.pxar` | Explicit `/etc/pve` pmxcfs mount |
| `pve-cluster.pxar` | Consistent online SQLite backup of `/var/lib/pve-cluster/config.db` |

All three archives are encrypted. This is a **configuration backup**, not a VM,
CT, whole-host or boot-disk backup. Root's home/SSH files, custom scripts outside
`/etc`, boot partitions and other nested mounts require separate coverage.
The SQLite snapshot is consistent individually; it is not an atomic snapshot
with the live `/etc/pve` tree. Avoid configuration changes during backup windows.
Restoring `config.db` requires the vendor's pmxcfs recovery procedure on an
isolated replacement, not overwriting the database on a running node.

`Persistent=true` can trigger a missed backup when the timer is enabled. To run
and inspect a first backup explicitly:

```sh
systemctl start anansi-pve-config-backup.service
journalctl -u anansi-pve-config-backup.service --no-pager
systemctl list-timers anansi-pve-config-backup.timer
```

Wire `pve_hardening_backup_on_failure` to an existing notification `.service`
unit or alert externally on failures. There is no email integration by default.
Configure PBS retention, verification, off-site synchronization and monitoring
separately. Use `proxmox-backup-client snapshot list`, then restore an explicit
`host/<node>/<timestamp>` and archive into an isolated directory with the
matching key. Follow the installed client's `restore --help`; the supplied
guide's restore example omits the required snapshot argument.

## Verification and recovery

After applying enabled controls, check `fail2ban-client status anansi-proxmox`,
`rsyslogd -N1`, `journalctl --disk-usage`, `auditctl -l`, KSM `run` and
`pages_sharing`, and the backup job/result. Verify real log delivery, a controlled
GUI ban and an encrypted restore. Test guest networking, console access and
backup jobs before and after a maintenance reboot. Report output contains host
configuration and guest inventory; retain Ansible logs appropriately.

To retire a control, remove its specifically named Anansi configuration after
review and reload the owning service. Disable the backup timer before removing
its units. For KSM, remove its tmpfiles fragment and unmask/re-enable the KSM
services only if you intend to resume merging. Keep encryption keys until all
backups that use them expire. The role deliberately has no broad cleanup or
automatic rollback of independent services.

Local checks (no host connection):

```sh
ansible-playbook -i roles/proxmox-hardening/examples/hosts.yml \
  proxmox-hardening.yml --syntax-check
python3 roles/proxmox-hardening/tests/test_role.py
```

The tests need PyYAML and Jinja2 in the chosen Python environment. They cover
tag/gating structure, template rendering and backup failure/secret handling.
Live PVE 9.2, HPE firmware, Fail2Ban action and pmxcfs audit validation remain
host-side checks.
