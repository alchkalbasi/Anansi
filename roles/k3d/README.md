# k3d

Installs the K3d CLI, renders a K3d cluster configuration, and creates the
configured K3s-in-Docker cluster by default.

## Requirements

- A Debian or Ubuntu amd64 or arm64 target.
- Docker must be installed and available to `k3d_user` before the cluster is
  created. K3d requires Docker; the role deliberately does not install it.
- Kubectl is recommended for interacting with the created cluster.

## Role variables

- `k3d_version`: K3d GitHub release to install; defaults to `v5.9.0`.
- `k3d_install_dir`: binary installation directory; defaults to
  `/usr/local/bin`.
- `k3d_user`: account that owns the generated kubeconfig and runs K3d;
  defaults to the Ansible connection user.
- `k3d_home`: home directory for that account; defaults to its passwd entry.
- `k3d_completion_enable`: enable completion for each selected user's login
  shell; defaults to `true`.
- `k3d_target_users`: users to configure; leave empty (the default) to use the
  Ansible connection user. Bash and Zsh are supported.
- `k3d_config_path`: rendered configuration destination; defaults to
  `/etc/k3d/k3d-config.yml`.
- `k3d_cluster_name`: name of the cluster; defaults to `k3d`.
- `k3d_cluster_config`: complete mapping rendered as K3d configuration YAML.
- `k3d_cluster_create`: create the configured cluster when `true`; defaults to
  `true`.

The default cluster has one server, one agent, and exposes its Kubernetes API
only on `127.0.0.1:6445`. Override the complete configuration where a
different topology or port mapping is required.

## Example playbook

```yaml
---
- name: Install, configure, and create k3d
  hosts: workstations
  gather_facts: true
  become: true
  roles:
    - role: k3d
```

Cluster creation is idempotent and is available through the `k3d-cluster` tag.
Shell completion is available through the `k3d-completion` tag. Set
`k3d_cluster_create: false` to install and render only.

## License

MIT
