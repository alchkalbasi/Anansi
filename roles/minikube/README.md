# minikube

Installs the Minikube CLI, configures its global settings, and can optionally
create a Minikube profile.

## Requirements

- A Debian or Ubuntu amd64 or arm64 target.
- Docker must be installed before creating a profile with the default Docker
  driver.
- The role gathers the required OS and architecture facts itself.

## Role variables

- `minikube_version`: Minikube GitHub release to install; defaults to
  `v1.37.0`.
- `minikube_checksums`: SHA-256 values for that release. Update these when
  changing `minikube_version`.
- `minikube_install_dir`: binary installation directory; defaults to
  `/usr/local/bin`.
- `minikube_user`: account that owns and runs Minikube; defaults to the
  Ansible connection user.
- `minikube_home`: Minikube configuration directory; defaults to that user's
  home directory plus `/.minikube`.
- `minikube_config`: global Minikube settings; defaults to the Docker driver.
- `minikube_completion_enable`: enable completion for each target user's login
  shell; defaults to `true`.
- `minikube_target_users`: users to configure; leave empty (the default) to
  configure the Ansible connection user. Bash and Zsh are supported.
- `minikube_profile`: profile name to create; defaults to `minikube`.
- `minikube_kubernetes_version`: Kubernetes version used for the profile;
  defaults to `stable`.
- `minikube_cluster_create`: when `true`, create or start the configured
  profile; defaults to `false`.
- `minikube_enabled_addons`: addons enabled after the profile is available;
  defaults to `['metrics-server']`.

## Example playbook

```yaml
---
- name: Install and configure minikube
  hosts: workstations
  gather_facts: true
  become: true
  roles:
    - role: minikube
      minikube_cluster_create: true
```

The profile lifecycle task is available through the `minikube-cluster` tag;
it also enables `minikube_enabled_addons`.

## License

MIT
