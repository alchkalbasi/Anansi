<p align="center">
  <img src="https://github.com/MHSanaei/3x-ui/raw/main/media/3x-ui-dark.png" alt="3xui-logo"/>
</p>

# 3x-ui Deployment Stack

This is an **Ansible role** paired with a **Docker Compose** stack to automate the deployment and provisioning of the `3x-ui` panel.

The playbook validates the target environment, prepares the directory structures, manages required environment variables, and launches the container utilizing **Host Networking Mode** to efficiently handle dynamic Xray inbound routing.

---

## Prerequisites

Before executing the playbook, ensure the target host meets the following requirements:

* **Operating System:** Linux (Ubuntu/Debian recommended)
* **Dependencies:** `docker-ce` and `docker-compose-plugin` installed.
* **Ansible Collections:** `community.docker` installed on your control node.

---

## Configuration & Variables

The Ansible role relies on the following variables. Define these in your `group_vars`, `host_vars`, or directly inside your playbook:

### Ansible Role Variables

| Variable | Description | Example |
| --- | --- | --- |
| `service_dir` | Remote host target directory for deployment | `/opt/3x-ui` |
| `docker_networks` | Array of external docker networks to pre-create | `['proxy-net']` |

### Environment Variables (`.env.j2`)

The playbook dynamically templates the `.env` file using these variables:

* `XUI_DOCKER_IMAGE`: The 3x-ui image version (e.g., `ghcr.io/mhsanaei/3x-ui:latest`).
* `XUI_CONTAINER_NAME`: Name for the container (e.g., `3x-ui`).
* `XUI_LOG_LEVEL`: Operational logging level (`debug`, `info`, `warn`, `error`).
* `XUI_ENABLE_FAIL2BAN`: Protect panel with fail2ban integration (`true` / `false`).
* `XUI_RESTART_POLICY`: Container recovery behavior (e.g., `unless-stopped`).

---

## Usage

### 1. Execute the Entire Deployment

Run the playbook against your target inventory group:

```bash
ansible-playbook -i inventory.ini playbook.yml

```

### 2. Targeted Execution Using Tags

The tasks are highly modular and can be targeted using Ansible tags:

* **Verify Environment Only:**
```bash
ansible-playbook -i inventory.ini playbook.yml --tags "check-docker"

```


* **Update Files & Configurations Only:** (Copies Compose and updates `.env`)
```bash
ansible-playbook -i inventory.ini playbook.yml --tags "preparing"

```


* **Trigger Only Deployment/Restart:**
```bash
ansible-playbook -i inventory.ini playbook.yml --tags "deploy"

```

---

> ⚠️ **Network Note:** Because the Compose configuration utilizes `network_mode: host` to streamline Xray port mappings, the container shares the host network stack directly. Ensure firewall ports (like the panel web UI port) are secured or exposed on your target server accordingly.