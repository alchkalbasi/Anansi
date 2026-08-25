kubectl
=======

Installs and configures `kubectl` on Debian/Ubuntu hosts: the modern
`pkgs.k8s.io` APT repo, bash completion, a `k` alias, and a set of
commonly used kubectl add-on tools (fzf, Krew + common plugins,
kubectx/kubens, kubecolor, kubeval, kail, kube-shell, kube-ps1).

The legacy `apt.kubernetes.io` repo (apt-key based) that older kubectl
install guides use is shut down upstream, so this role uses the current
per-minor-version `pkgs.k8s.io` repo instead.

Requirements
------------

Debian or Ubuntu, with APT and a user account to configure shell
integration for (see `kubectl_target_users`).

Role Variables
--------------

See [defaults/main.yml](defaults/main.yml) for the full, commented list.
Highlights:

- `kubectl_target_users` (`['debian']`): Linux users to configure aliases,
  completion, Krew, kube-ps1, etc. for.
- `kubectl_k8s_minor_version` (`"1.36"`): Kubernetes minor version branch
  of the `pkgs.k8s.io` repo kubectl is installed from. Bump to upgrade.
- `kubectl_pin_version` (`false`): hold the `kubectl` package at its
  currently installed version after install.
- `kubectl_alias_name` (`k`) / `kubectl_extra_aliases`: shell aliases
  added to each target user's `~/.bashrc`.
- `kubectl_fzf_enable`, `kubectl_krew_enable`, `kubectl_kubecolor_enable`,
  `kubectl_kubeval_enable`, `kubectl_kail_enable`,
  `kubectl_kube_shell_enable`, `kubectl_kube_ps1_enable`: toggle each
  add-on independently. `kubectl_kubectx_kubens_aliases_enable` depends on
  `kubectl_krew_enable` since it aliases the `ctx`/`ns` Krew plugins.
- `kubectl_krew_plugins`: list of Krew plugins installed for each target
  user (defaults to `ctx`, `ns`, `tree`, `neat`, `score`, `deprecations`,
  `df-pv`, `images`).

Tags follow the `kubectl`, `kubectl-install`, `kubectl-config`,
`kubectl-addons`, `kubectl-<addon-name>` convention, so any part can be
run in isolation, e.g. `--tags kubectl-krew`.

Notes
-----

- kubeval is unmaintained upstream and only ships amd64/386 Linux
  binaries; it is skipped automatically on other architectures.
- kube-ps1 is only configured for target users that already have Oh My
  Zsh installed (`~/.oh-my-zsh`); otherwise it's skipped for that user.
- Krew and its plugins are installed per-user under `~/.krew` (not
  system-wide), matching upstream Krew's design.
- kube-shell is installed in an isolated virtual environment at
  `/opt/kube-shell/venv` and exposed as `/usr/local/bin/kube-shell`. This
  avoids replacing Debian-managed Python packages such as `click`.

Example Playbook
----------------

```yaml
- hosts: workstations
  become: true
  roles:
    - role: kubectl
      kubectl_target_users: ['alch']
      kubectl_k8s_minor_version: "1.36"
      kubectl_pin_version: true
```

License
-------

MIT-0
