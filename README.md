# Anansi

<p align="center">
  <img src="./images/anansi-logo.png" alt="Anansi logo" title="Anansi" height="300" />
</p>

<p align="center"><em>Many hands, One mind.</em></p>

Anansi is a collection of reusable Ansible roles for automating everyday
DevOps and infrastructure tasks. The repository includes roles for system
configuration, containerized services, databases, Kubernetes tooling,
networking, observability, and collaboration platforms.

## What is included?

- **Infrastructure and system setup:** Docker, iptables, downloads, and
  general host setup.
- **Applications and services:** Jitsi, Confluence, Mattermost, NetBox,
  3x-ui, MinIO, RustFS, and web services.
- **Databases:** MySQL and PostgreSQL master/slave replication roles.
- **DevOps platforms:** GitLab, GitLab Runner, and the ELK stack.
- **Kubernetes tooling:** `kubectl` installation, shell integration, and
  optional productivity add-ons.
- **Observability:** InfluxDB, Telegraf, and Prometheus-related roles.

Each role keeps its own documentation, defaults, templates, files, and task
entry point. Start with the role-specific `README.md` and
`defaults/main.yml` before deploying it.

## Requirements

- Ansible installed on the control machine.
- SSH access to the target hosts.
- `become` privileges for roles that install packages or manage services.
- Role-specific dependencies such as Docker Engine, Docker Compose, or the
  `community.docker` collection where documented.

Install the collections used by a role before running it. For example:

```bash
ansible-galaxy collection install community.docker
```

## Usage

Clone the repository, review the selected role's variables, and run a
playbook against your inventory:

```bash
git clone <repository-url> anansi
cd anansi
ansible-playbook -i inventory.ini playbook.yml
```

The root [`playbook.yml`](playbook.yml) contains example host groups and role
invocations. Adapt its hosts, variables, and secrets to your environment
before using it. For a focused deployment, create a small playbook that
includes only the role you need:

```yaml
---
- name: Configure Kubernetes tools
  hosts: workstations
  become: true
  roles:
    - role: kubectl
      kubectl_target_users:
        - your-user
```

Run selected tasks with tags when the role provides them:

```bash
ansible-playbook -i inventory.ini playbook.yml --tags kubectl-addons
```

## Repository layout

```text
.
├── playbook.yml       # Example entry point
├── roles/             # Reusable Ansible roles
├── images/            # Project assets
└── LICENSE            # MIT license
```

Role documentation is available in the corresponding directory, for
example [`roles/kubectl/README.md`](roles/kubectl/README.md) and
[`roles/jitsi/README.md`](roles/jitsi/README.md).

## Security notes

Do not commit passwords, private keys, API tokens, or production inventory
data. Store secrets with Ansible Vault or an approved secret-management
system, and review role defaults and generated Compose files before applying
changes to a production host.

## License

Anansi is released under the [MIT License](LICENSE).
