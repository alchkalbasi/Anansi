# Guide coverage and deployment decisions

The supplied guide is reference material, not an instruction to execute every
command. Scope: one standalone Gen10, no Ceph. Controls below marked manual are
not configured by this role and remain part of completing the host hardening.

| Guide section | Implementation / required follow-up |
| --- | --- |
| 1.1.1–1.1.2 CIS Debian profiles | Partial selected controls only. Full CIS assessment is manual; preserve FUSE, storage modules, guest networking and PVE service access. Do not include the generic linux-hardening role without a PVE-specific review. |
| 1.1.3 Automatic security updates | `updates`; Debian security only, PVE/kernel exclusions, no auto-removal/reboot. |
| 1.1.4 SSH audit | `sshd` opt-in global key-only policy with timed rollback; review Match exceptions below. No key regeneration. |
| 1.1.5–1.1.6 Encryption and storage partitions | Installation/maintenance work; never repartition live disks or remount `/var/lib/vz` automatically. |
| 1.1.7 Firmware repository | Manual review of existing Debian deb822 sources; retain subscription configuration. |
| 1.1.8 CPU microcode | `microcode`; vendor detected, reboot scheduled separately. |
| 1.2.1 Secure Boot / lockdown | Read-only observations; firmware/bootloader changes manual, using the actual boot path. |
| 1.2.2 Network separation | Manual management/iLO/storage/guest VLAN and switch configuration. |
| 1.2.3 Subscription | Operational choice; repositories/license unchanged. |
| 1.2.4–1.2.5 PVE firewall | Manual native firewall policy below, or opt-in templated host iptables INPUT rules with timed rollback. No backend switch or raw FORWARD policy replacement. |
| 1.2.6 KSM | `ksm`; stops new merging, optional guarded unmerge. Per-VM Allow KSM settings reviewed separately. |
| 1.2.7–1.2.8 VM/container isolation | Manual workload design and privilege review; no conversion/removal of existing containers. |
| 1.3 SDN | Manual only if used. Do not blindly disable IP forwarding on routed/NAT/SDN hosts. |
| 2.1 Accounts, RBAC, MFA, emergency access | Manual enrollment and least-privilege assignment through PVE; no root locking, PAM rewrites, or broad ACL grants. |
| 2.2 API tokens | Manual token creation, scoped ACLs, secret storage and rotation. `--expire` takes a Unix epoch, not a date string. |
| 2.3.1–2.3.2 Certificates/renewal | Configure native PVE ACME with your DNS/FQDN/provider; no replacement of cluster CA files. |
| 2.3.3 GUI Fail2Ban | `fail2ban`; anchored journal filter, explicit trusted networks, GUI port only. |
| 3 Cluster and Ceph | Not applicable to the declared topology. The role rejects a configured Corosync cluster. |
| 4.1 3-2-1 backups | Operational PBS/off-site/immutable-storage policy; not achieved by a local timer alone. |
| 4.2 Host backup and encryption | `backup`; three encrypted config archives, existing escrowed key. |
| 4.3–4.4 Guest backups/encryption | Configure PVE guest backup jobs and encrypted PBS storage separately. |
| 4.5 Failure notifications | Optional systemd OnFailure hook; external alert delivery must be configured/tested. |
| 4.6 Restore drills | Manual quarterly isolated restores, documented RTO/RPO. |
| 5.1.1 Logging | `logging`; persistent journal, system log forwarding and GUI access log, TLS collector required. |
| 5.1.2 Auditd | `audit`; local pmxcfs watch, actual event coverage must be verified. |
| 5.2 Monitoring/alerts | Existing external monitoring stack: least-privilege PVE exporter/token, resource, backup, disk/RAID, certificate and hardware alerts. |
| 5.3 Audits/rootkit checks | Manual external audit schedule and evaluated tooling; no claim that rkhunter makes a compromised hypervisor trustworthy. |
| 5.4 Documentation/exceptions | Maintain node inventory, VLAN map, key escrow record, exceptions and restore results. |

## SSH and native firewall setup

Before changing SSH, test key access in a **new** session and verify iLO console
access. Keep port 22 and root key login available if future clustering is planned.
Review effective `sshd -T -C user=root,host=<name>,addr=<admin-IP>` output,
including Match blocks and include precedence. For a key-only root policy use
`PermitRootLogin prohibit-password` with `PubkeyAuthentication yes`; only disable
password/keyboard-interactive authentication globally after all required admin
accounts have working keys and no SSH MFA dependency. Validate the full config
with `sshd -t` before reload and test a new SSH connection before closing the old
session. Do not blindly restrict TCP forwarding or replace PVE's SSH keys and
symlinks. The optional `sshd` control implements the global key-only policy; existing
Match exceptions remain subject to manual review. See [README.md](README.md#ssh-server).

Use the native PVE firewall after documenting actual IPv4/IPv6 administration
and storage paths. Keep recovery access open while making these changes:

1. In Datacenter/Node Firewall, allow TCP 8006 and TCP 22 only from actual trusted
   administrator/VPN sources. Add other required sources/services (SPICE, storage,
   monitoring) explicitly. Review existing node-level rules and automatic PVE
   allowances; an INPUT DROP policy alone is not proof that only your list is allowed.
2. Review the automatically inferred `local_network` and the `management` IP set.
   On a publicly addressed standalone host, don't implicitly trust an entire
   provider subnet. Scope the local alias and management set to intended hosts.
3. Enable the firewall at Datacenter and Node scope with INPUT DROP and OUTPUT
   ACCEPT. Compile/inspect the active backend and test new SSH/GUI access from
   allowed **and disallowed** IPv4/IPv6 sources through an independent connection.
4. Enable guest firewall and per-NIC flags only with reviewed guest rules. A
   host policy does not protect all guest traffic automatically. FORWARD/VNet
   rules are backend-dependent; never change the backend or drop forwarded
   traffic without guest connectivity testing.

This role's GUI Fail2Ban jail supplements this policy; it is not a default-deny
host firewall. Native PVE firewall automation remains outside this role. The optional `iptables`
control is an alternative host INPUT policy and requires the native firewall to
be inactive. Document management source addresses, storage paths and a tested
recovery strategy before enabling either path.

## HPE Gen10 operations

Treat iLO as a separate management device; host Ansible cannot establish its
security from OS settings alone. Verify the exact server model and iLO firmware:

- Put the dedicated iLO port on an isolated management network reached through
  a VPN/bastion. Restrict access upstream; keep it off the public Internet.
- Apply model-specific HPE System ROM, iLO, NIC and storage-controller firmware
  in a maintenance window with verified backups and console access.
- Replace default/shared iLO credentials with named least-privilege accounts,
  review remote console/virtual media access, configure trusted HTTPS and time.
- Disable unused management services, especially IPMI/DCMI over LAN where
  nothing requires it. Review the iLO security dashboard and its security state
  against the integrations you actually use.
- Verify UEFI boot mode, Secure Boot chain and signed drivers before enabling
  Secure Boot or lockdown. PVE boot configurations differ; never assume GRUB.
- Monitor controller/drive health, cache protection, power supplies, temperature,
  and firmware events externally. CPU microcode alone does not update iLO/ROM.

## Corrections to the guide's examples

- The security-update example also allows the general Debian origin. This role
  selects only Debian Security and leaves PVE updates to a maintenance window.
- PBS skips nested mount points. This role explicitly archives `/etc/pve` and
  uses SQLite's backup API for `config.db`; simply archiving `/etc` is insufficient.
- PBS token IDs use `user@realm!token`, and token expiration is a Unix epoch.
  Restore operations need a snapshot, an archive name and a target.
- VNet firewall rules use the FORWARD direction, not generic INPUT/OUTPUT
  defaults. Do not copy the guide's SDN sysctls into a routed host.
- KSM unmerge can increase RAM consumption immediately. Stop-only is the default.
- Realm-wide MFA and root emergency-access exceptions require an enrollment
  plan; blindly applying a realm-wide flag can conflict with emergency access.
- Auditd rules on FUSE need live validation. Configuration-file presence alone
  is not evidence that pmxcfs changes are fully audited.

## Primary references checked during implementation

- [Proxmox native firewall documentation](https://github.com/proxmox/pve-docs/blob/master/pve-firewall.adoc)
- [Proxmox cluster and SSH documentation](https://github.com/proxmox/pve-docs/blob/master/pvecm.adoc)
- [PBS backup-client usage and mount handling](https://pbs.proxmox.com/docs/backup-client.html)
- [Rsyslog TLS forwarding](https://docs.rsyslog.com/doc/configuration/modules/omfwd.html)
- [HPE recommended iLO 5 security settings](https://support.hpe.com/hpesc/public/docDisplay?docId=a00026171en_us&page=GUID-86270520-4C59-457F-944E-C667D5564EA8.html)

Use the documentation matching the installed PVE/PBS/firmware versions when
performing manual changes; these upstream references can change over time.
