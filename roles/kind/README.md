# kind

Installs the Kind CLI and renders a Kind cluster configuration file from an
Ansible variable through a Jinja2 template. This first step does not create or
delete a cluster.

## Requirements

- A Debian or Ubuntu amd64 or arm64 target.
- Docker or another Kind-compatible container provider must be installed before
  creating a cluster.
- The role gathers the required OS and architecture facts itself.

## Role variables

- `kind_version`: Kind release to install; defaults to `v0.32.0`.
- `kind_install_dir`: binary installation directory; defaults to
  `/usr/local/bin`.
- `kind_config_path`: rendered configuration destination; defaults to
  `/etc/kind/kind-config.yml`.
- `kind_cluster_name`: name used by the default cluster configuration.
- `kind_cluster_config`: complete mapping rendered as Kind configuration YAML.

For example, a cluster with one worker and a host port mapping can be defined
as follows:

```yaml
kind_cluster_name: development
kind_cluster_config:
  apiVersion: kind.x-k8s.io/v1alpha4
  kind: Cluster
  name: "{{ kind_cluster_name }}"
  nodes:
    - role: control-plane
      extraPortMappings:
        - containerPort: 80
          hostPort: 8080
          protocol: TCP
    - role: worker
```

## Example playbook

```yaml
---
- name: Install and configure kind
  hosts: workstations
  gather_facts: true
  roles:
    - role: kind
```

The rendered config can then be used explicitly:

```bash
kind create cluster --config /etc/kind/kind-config.yml
```

## License

MIT
