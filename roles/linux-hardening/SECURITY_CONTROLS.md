# New security controls and operational impact

This file documents controls added during the 2026-09 security review. A
configuration control is not presented as a substitute for a vendor kernel or
package update. Controls that reduce access to a vulnerable subsystem are
attack-surface reduction or temporary mitigation only.

## Package and reboot remediation

| Variable | Change and security value | Compatibility and reboot |
| --- | --- | --- |
| `linux_hardening_allow_package_upgrade` | When exactly `true`, refreshes APT metadata and performs `apt` safe-upgrade. This is the primary remediation path for kernel, OpenSSH, libc, and other package CVEs. It does not run a release/distribution upgrade. | Default `false`. Package upgrades can restart services. Kernel or low-level library updates can require reboot. |
| `linux_hardening_allow_reboot` | Reboots only when `/var/run/reboot-required` exists after the authorized upgrade. The role reports packages listed in `/var/run/reboot-required.pkgs` first. | Default `false`. A reboot occurs only when both package upgrade and reboot permission are true. |
| `linux_hardening_package_cache_valid_time` | Bounds APT metadata refresh frequency while preserving idempotence. | No reboot. Default 3600 seconds. |
| `linux_hardening_reboot_timeout` | Bounds the Ansible reboot and reconnect operation. | No effect unless a reboot is authorized. |

The update workflow uses repository versions selected by the host's configured
APT sources. Operators remain responsible for supported releases, correct
security repositories, phased-update policy, third-party repositories, and a
serial maintenance window.

## Kernel sysctl attack-surface controls

Every entry below additionally requires `linux_hardening_kernel_parameters:
true`. All new entries default to `enabled: false`.

| Entry and proposed value | Classification and rationale | Compatibility / reboot |
| --- | --- | --- |
| `kernel.dmesg_restrict=1` | Defense in depth. Restricts unprivileged kernel-log access and reduces kernel address/state disclosure useful in exploitation. | Affects non-root diagnostics. No reboot. |
| `kernel.perf_event_paranoid=3` | Attack-surface reduction. Restricts unprivileged performance events and kernel profiling interfaces. | Can break application profilers, monitoring agents, and developer tooling. No reboot. |
| `kernel.kexec_load_disabled=1` | Attack-surface reduction. Prevents loading a replacement kernel through kexec. | Breaks kexec/kdump workflows unless the crash image is prepared first. One-way for the running boot; reboot is required to reverse it. |
| `kernel.sysrq=0` | Defense in depth. Disables the Magic SysRq interface. | Can remove an important emergency-recovery tool. No reboot to apply; review console operations first. |
| `kernel.unprivileged_bpf_disabled=1` | Configuration mitigation and attack-surface reduction for unprivileged eBPF verifier/JIT vulnerabilities, including the class represented by CVE-2023-2163 and CVE-2022-23222. | Can break unprivileged tracing/network tools. Value 1 cannot be reversed until reboot. Privileged BPF remains available. A patched kernel is still required. |
| `kernel.unprivileged_userns_clone=0` | Configuration mitigation and attack-surface reduction for exploits that require an unprivileged user namespace, including Canonical's documented mitigation for CVE-2024-1086. | Breaks rootless containers and some browser/application sandboxes. Debian/Ubuntu-specific key. No reboot. A patched kernel is still required. |
| `user.max_user_namespaces=0` | Portable additional restriction on creating user namespaces. | Breaks rootless containers, Kubernetes/container build tools, and sandboxing. It is broader than the Debian/Ubuntu-specific key. No reboot. |
| `kernel.io_uring_disabled=2` | Attack-surface reduction for the io_uring vulnerability class, including CVE-2025-39698. | Disables new io_uring instances for all processes and can reduce performance or break databases, runtimes, and storage software. Kernel support varies; no reboot. A patched kernel is still required. |
| `vm.unprivileged_userfaultfd=0` | Attack-surface reduction. Restricts unprivileged userfaultfd use, an exploitation primitive in multiple memory-management attacks. | Can affect QEMU, checkpoint/restore, live migration, and specialized runtimes. No reboot. |
| `vm.mmap_min_addr=65536` | Defense in depth against null-page mapping techniques used by some kernel exploits. | Can break legacy software requiring low mappings. No reboot. |

The existing `kernel.kptr_restrict`, `kernel.yama.ptrace_scope`, ASLR, protected
link/FIFO/file, core-dump, routing, redirect, source-route, reverse-path, ICMP,
and SYN-cookie controls remain unchanged.

## Kernel module restrictions

`linux_hardening_modules` now also offers disabled-by-default policies for:

- legacy protocols: `ax25`, `netrom`, `rose`, `x25`, `atm`, `can`;
- device-facing subsystems: `bluetooth`, `btusb`, `firewire_core`,
  `firewire_ohci`, `thunderbolt`, `usb_storage`, `uvcvideo`;
- uncommon filesystems: `adfs`, `affs`, `befs`, `bfs`, `exofs`, `hpfs`,
  `minix`, `nilfs2`, `omfs`, `qnx4`, `qnx6`, `sysv`, `ufs`.

This is attack-surface reduction for systems that do not need those features.
It is relevant to recurring filesystem, Bluetooth, and USB memory-safety CVE
classes, but it does not patch CVE-2025-39860, CVE-2025-38555, or any other
specific defect. A module policy prevents future loads; it does not unload an
active module and does not disable a subsystem compiled into the kernel.
`linux_hardening_refresh_initramfs` controls whether changed policies are
included in initramfs. Removing a policy from initramfs or reversing an active
block can require a reboot. Device access, storage, network stacks, and
container workloads must be inventoried before enabling these entries.

## Audit rules

`linux_hardening_audit_rules_enabled` installs a root-only augenrules fragment
covering changes to identity databases and audit configuration plus hostname,
time, mount, and kernel-module syscalls. Existing rules owned by other files
are not deleted. Optional sudo/password-history paths are watched only when
they exist. The handler loads the compiled rule set after changes.

`linux_hardening_audit_immutable` appends `-e 2`. This prevents all audit-rule
changes for the remainder of the boot, even by root. It defaults to `false` and
requires a reboot before rules can be changed after it has been loaded. Audit
rules can increase log volume and syscall overhead; immutable mode complicates
incident response and staged configuration changes.

These are detection and tamper-resistance controls, not CVE remediation.

## Privilege, service, and mandatory-access controls

| Variable | Change and rationale | Compatibility / reboot |
| --- | --- | --- |
| `linux_hardening_sudo_policy_enabled` | Installs a `visudo`-validated drop-in enabling a pseudo-terminal, a dedicated sudo log, and bounded credential-cache/password-prompt timeouts. This improves command attribution and reduces unattended privilege reuse. | Default `false`; can affect non-interactive automation and logging capacity. No reboot. Controlled by the logfile and timeout variables. |
| `linux_hardening_apparmor_install` | Installs AppArmor userspace packages without package-triggered service activation. | Default `false`. Installing packages does not prove the LSM is active in the booted kernel. |
| `linux_hardening_apparmor_service` | Starts and enables the AppArmor service. | Default `false`; profiles can affect applications. Enabling the kernel LSM itself may require bootloader changes and reboot, which this role does not make. |
| `linux_hardening_disable_services` | Stops, disables, and masks only the exact units in `linux_hardening_disabled_services`. Reduces remotely reachable and privileged code. | Default `false` with an empty list. A wrong unit selection can cause an outage. No automatic discovery or broad service removal occurs. |

## SSH additions

The existing transactional SSH engine can now manage three additional native
directives, all disabled by default:

- `PermitUserRC no` prevents `~/.ssh/rc` execution, useful for forced-command
  and restricted accounts but incompatible with users that rely on that hook;
- `ExposeAuthInfo no` avoids exposing authentication-method details in the
  session environment;
- `PermitTTY no` removes interactive terminals on automation/SFTP-only hosts
  and must not be enabled on interactive administration servers.

These are defense-in-depth settings. OpenSSH defects such as CVE-2024-6387
require a patched `openssh-server`; `LoginGraceTime 0` is intentionally not
made a default because the vendor-documented workaround trades RCE exposure
for denial-of-service risk.

## Firewall and filesystem safety checks

`iptables_hardening_container_networking_acknowledged` must be `true` before
the role applies a default FORWARD `DROP` policy on a host where common Docker
or Kubernetes/CNI state is detected. It is a deployment-safety acknowledgement,
not an allowance rule. Operators must inspect the container runtime's chains
and traffic paths. Existing non-flushing rule merge, restore validation,
rollback timer, fresh SSH connection test, and post-verification persistence
remain in place.

Mount hardening now treats `findmnt` return code 1 as "not a mountpoint" and
fails with an actionable message before parsing JSON or creating an `fstab`
entry. Directory-permission controls remain independent. This prevents a
configuration error; it is not a CVE mitigation.

## Authoritative references

- [Linux kernel self-protection guidance](https://docs.kernel.org/security/self-protection.html)
- [Linux kernel sysctl documentation](https://docs.kernel.org/admin-guide/sysctl/kernel.html)
- [Linux Yama ptrace documentation](https://docs.kernel.org/admin-guide/LSM/Yama.html)
- [ANSSI GNU/Linux configuration recommendations](https://messervices.cyber.gouv.fr/guides/en-configuration-recommendations-gnulinux-system)
- [Debian guidance on continuous security updates](https://www.debian.org/doc/manuals/securing-debian-manual/ch10.en.html)
- [Ubuntu security update guidance](https://documentation.ubuntu.com/security/security-updates/)
