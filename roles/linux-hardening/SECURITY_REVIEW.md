# Linux hardening security review

Review date: 2026-09-20

Scope: every task, handler, default, fixed variable, template, role-local module,
test, and documentation file under `roles/linux-hardening`. The supported
platform remains Debian 12/13 and Ubuntu 22.04/24.04/26.04. CVE status is
distribution- and kernel-flavour-specific; the version running on a host must
be compared with its vendor tracker rather than with upstream version numbers
alone.

## Existing controls found

The role already had substantial coverage and those working controls were
retained:

- core dumps disabled across PAM limits, systemd-coredump, and login shells;
- Ctrl-Alt-Delete masking, cron/passwd/shadow permissions, executable PATH
  write restriction, securetty, umask/timeout, removal of legacy packages and
  trust files, account locking/ageing/home permissions, duplicate UID 0
  removal, and gated SUID/SGID policy;
- configurable login.defs, passwdqc, faillock, PAM `no_pass_expiry`, and
  password hash policy;
- sysctl support for filesystem link protection, ASLR, pointer exposure,
  ptrace, routing, reverse-path filtering, source routing, redirects, ICMP,
  SYN cookies, TCP hardening, and IPv6 policy;
- module blocking for uncommon filesystems and DCCP/RDS/SCTP/TIPC, with mounted
  filesystem and EFI checks and optional initramfs refresh;
- separately gated mount options and directory permissions;
- auditd installation/service/configuration and journald audit-socket policy;
- transactional OpenSSH server editing with Include preservation, `sshd -t`,
  timed rollback, fresh authenticated connection verification, and safe port
  handoff; native SSH client validation with `ssh -G`; strong authentication,
  forwarding, cipher/MAC/KEX, host-key, moduli, banner, and file permission
  controls;
- non-flushing iptables/ip6tables filter-table merging that preserves foreign
  chains/rules, validates restore input, protects remote SSH, uses a rollback
  watchdog, and persists only after runtime and connection verification;
- strict YAML-boolean and nested-control validation plus focused offline tests.

## Gaps found

The role did not have an operator-authorized package update mechanism, reboot
reporting/control, kernel audit rules, sudo policy, AppArmor lifecycle controls,
generic service reduction, modern io_uring/eBPF/userfaultfd/perf/dmesg controls,
or optional Bluetooth/USB/legacy filesystem modules. It also did not guard a
FORWARD DROP policy on detected container hosts. Mount discovery attempted to
parse `findmnt` output without first treating return code 1 as a normal
"not a mountpoint" result.

The documentation claimed that all shipped defaults were false, but the
current checkout contains an opinionated active default profile. That mismatch
was corrected in the main README; new disruptive controls remain false. A
separate explicit no-op test profile now prevents accidental local mutation.

## Controls added

- explicit APT safe-upgrade gate, cache refresh, update reporting, reboot
  detection, reboot-package reporting, and independent reboot authorization;
- optional restrictions for dmesg, perf, kexec, SysRq, unprivileged eBPF,
  user namespaces, io_uring, userfaultfd, and low memory mappings;
- optional Bluetooth, USB, FireWire, Thunderbolt, camera, legacy protocol, and
  uncommon filesystem module blocks;
- additive audit rules for identity/audit configuration plus hostname, time,
  mount, and module syscalls; optional irreversible-for-the-boot audit mode;
- `visudo`-validated sudo pseudo-terminal/logging/credential timeout policy;
- optional AppArmor installation/service activation and explicit systemd unit
  masking;
- disabled-by-default SSH `PermitUserRC`, `ExposeAuthInfo`, and `PermitTTY`
  controls;
- container-networking acknowledgement before managed FORWARD DROP;
- safe mountpoint failure before JSON parsing or `fstab` mutation.

[SECURITY_CONTROLS.md](SECURITY_CONTROLS.md) provides variable-by-variable
rationale, compatibility impact, and reboot behavior.

## CVE and vulnerability-class review

| Vulnerability | Exposure and affected versions where reliably stated | Role treatment | Primary remediation |
| --- | --- | --- | --- |
| [CVE-2026-64531](https://ubuntu.com/security/CVE-2026-64531) | High-priority Open vSwitch nested-action length flaw that can cause the kernel to interpret a malformed action stream. Canonical lists Ubuntu generic kernels fixed at 7.0.0-30.30 (26.04) and 6.8.0-138.138 (24.04). | No generic configuration is claimed as a fix. Open vSwitch can be fundamental to cloud/container networking, so the role does not disable it based only on the CVE. | Install the fixed vendor kernel and reboot/livepatch as applicable; separately limit who can administer OVS. |
| [CVE-2024-1086](https://ubuntu.com/security/CVE-2024-1086) | nf_tables use-after-free enabling local privilege escalation. Canonical lists Ubuntu generic-kernel fixes at 5.15.0-101.111 (22.04) and 5.4.0-174.193 (20.04); 24.04 was not affected. Individual cloud/OEM flavours have separate rows. | Optional `kernel.unprivileged_userns_clone=0` implements Canonical's documented mitigation when user namespaces are unnecessary. The firewall implementation itself is not a fix. | Install the fixed vendor kernel and boot it. Namespace restriction is temporary mitigation/attack-surface reduction. |
| [CVE-2025-39698](https://ubuntu.com/security/CVE-2025-39698) | Unprivileged io_uring/futex use-after-free. Canonical lists generic Ubuntu 24.04 fixed at 6.8.0-94.96 and Ubuntu 22.04 HWE 6.8 fixed at 6.8.0-94.96~22.04.1; generic 22.04 was not affected. [Debian's tracker](https://security-tracker.debian.org/tracker/CVE-2025-39698) lists vulnerable code as absent from Bookworm and a Trixie fix at 6.12.48-1. | Optional `kernel.io_uring_disabled=2` removes new io_uring access but may break high-performance applications. | Install the vendor kernel. Disabling io_uring is attack-surface reduction, not a code fix. |
| [CVE-2023-2163](https://security-tracker.debian.org/tracker/CVE-2023-2163) | eBPF verifier error allowing arbitrary kernel read/write, privilege escalation, and container escape; Debian lists Bullseye fixed at 5.10.179-1 and unstable fixed at 6.1.27-1. | Optional `kernel.unprivileged_bpf_disabled=1`; privileged BPF remains available. | Install the fixed vendor kernel. Restricting unprivileged BPF mitigates the unprivileged path only. |
| [CVE-2023-0386](https://security-tracker.debian.org/tracker/CVE-2023-0386) | OverlayFS copy-up UID mapping flaw enabling local privilege escalation. Debian lists Bullseye fixed at 5.10.179-1 and upstream/unstable at 6.1.11-1; current Bookworm/Trixie packages are fixed. | User-namespace restrictions can reduce common exploitability, but OverlayFS is not blacklisted because containers commonly require it. | Patch the kernel. Do not disable OverlayFS on a general-purpose/container host merely for this CVE. |
| [CVE-2025-39860](https://ubuntu.com/security/CVE-2025-39860) | Bluetooth L2CAP socket cleanup use-after-free. Applicability depends on kernel version/configuration and Bluetooth reachability. | Optional `bluetooth`/`btusb` module blocking only for servers that do not use Bluetooth. | Install the fixed vendor kernel. Module blocking is only exposure reduction and does not affect built-in code. |
| [CVE-2025-38555](https://ubuntu.com/security/CVE-2025-38555) | USB gadget configfs use-after-free requiring `CAP_SYS_ADMIN` in the initial namespace. Canonical lists generic fixes at 6.8.0-100.100 (24.04) and 5.15.0-163.173 (22.04). | No false claim is made that blocking `usb_storage` fixes USB gadget code. Optional USB/device module policies reduce unrelated physical/device attack surface. | Install the fixed kernel; remove or restrict gadget functionality only when the actual platform does not require it. |
| [CVE-2024-6387](https://ubuntu.com/security/CVE-2024-6387) | OpenSSH pre-authentication race with potential remote code execution. Ubuntu fixes: 9.6p1-3ubuntu13.3 (24.04), 8.9p1-3ubuntu0.10 (22.04); [Debian Bookworm](https://security-tracker.debian.org/tracker/CVE-2024-6387) fixed at 9.2p1-2+deb12u3. | Package-upgrade gate provides remediation. Existing MaxStartups/LoginGraceTime controls remain. LoginGraceTime 0 is not imposed because the vendor warns that workaround exposes a MaxStartups exhaustion DoS. | Update `openssh-server`; no sshd configuration setting should be described as the preferred fix. |

The review also considered recurring memory corruption and use-after-free
classes in filesystems, Netfilter, networking protocols, Bluetooth, USB, and
drivers. General-purpose servers should not receive a growing blacklist keyed
only to CVE names. Features are offered only where an operator can reasonably
prove they are unused, while patching remains the universal remediation.

## Compatibility risks and settings intentionally optional

- user namespaces: rootless Docker/Podman, build tools, browser sandboxes, and
  some container runtimes;
- io_uring: databases, language runtimes, storage/network servers, and
  performance-sensitive applications;
- eBPF/perf: Cilium, observability, tracing, profiling, and security agents;
- userfaultfd: QEMU/KVM live migration, CRIU, and specialized runtimes;
- kexec: kdump and fast-reboot workflows; value 1 cannot be reversed in the
  current boot;
- IPv4/IPv6 forwarding, reverse-path filtering, IPv6 disabling, and FORWARD
  DROP: routers, VPNs, asymmetric routing, Docker, Kubernetes, and CNIs;
- module blocks: storage, removable media, cameras, Bluetooth, clustered and
  legacy filesystems/protocols; blacklist files do not unload active modules;
- audit immutable mode: prevents audit changes until reboot and complicates
  operational response; syscall auditing can add load and log volume;
- sudo pseudo-terminal/logging: automation behavior and log-capacity impact;
- AppArmor: enabling a service does not enable a missing kernel LSM and custom
  profiles can deny legitimate application access;
- service masking and SSH PermitTTY/UserRC: direct outage or administration
  risk if enabled without an inventory of dependencies.

These controls are disabled by default. Existing checkout-specific active
defaults were preserved rather than silently changing the deployed policy.

## Reboot requirements

Package upgrades report `/var/run/reboot-required` and never reboot unless
`linux_hardening_allow_reboot` is also true. A new kernel package does not
remediate the running kernel until that kernel is booted, unless an applicable
vendor livepatch is active. `kernel.kexec_load_disabled=1` and
`kernel.unprivileged_bpf_disabled=1` require reboot to reverse. Audit `-e 2`
requires reboot before changing loaded audit rules. Module blacklist changes
may require initramfs refresh and reboot to affect early-boot or currently
loaded modules.

## Recommended follow-up

1. Move the checkout's active role-default policy into inventory/group vars so
   reusable role defaults can eventually return to a conservative baseline
   without changing production intent.
2. Test Debian 12/13 and Ubuntu 22.04/24.04/26.04 in disposable VMs, including
   reboot convergence, audit rule loading, AppArmor state, SSH rollback, and
   both iptables backends.
3. Run a separate container-host profile with Docker/Kubernetes networking
   integration tests; do not use a generic FORWARD policy as proof of container
   isolation.
4. Add vendor vulnerability scanning (Debian Security Tracker/DSA and Ubuntu
   USN/OVAL) and verify the *running* kernel, not only installed packages.
5. Add AIDE or another file-integrity/EDR solution as a separate operational
   role with baseline storage and alert ownership; creating a database without
   monitoring would provide little protection.
6. Review Secure Boot, kernel lockdown, signed-module enforcement, encrypted
   storage, bootloader protection, centralized immutable logs, backup/restore,
   secrets management, and workload-specific systemd sandboxing outside this
   generic role.

## Reference baseline

The implementation follows the risk-based approach in the [Linux kernel
self-protection guide](https://docs.kernel.org/security/self-protection.html),
[ANSSI GNU/Linux configuration recommendations](https://messervices.cyber.gouv.fr/guides/en-configuration-recommendations-gnulinux-system),
[Debian security guidance](https://www.debian.org/doc/manuals/securing-debian-manual/),
and [Ubuntu security update guidance](https://documentation.ubuntu.com/security/security-updates/).
CIS and DISA STIG themes were used as comparison points, but controls were not
claimed as benchmark compliance and disruptive Level 2/site-policy items were
not enabled automatically.
