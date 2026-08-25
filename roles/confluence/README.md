<p><img src="https://upload.wikimedia.org/wikipedia/commons/thumb/8/88/Atlassian_Confluence_2017_logo.svg/512px-Atlassian_Confluence_2017_logo.svg.png?20210122192957" alt="confluence logo" title="Confluence" align="right" height="60" /></p>

# Ansible Role: Confluence Service

## Description

This role automates the deployment of **Atlassian Confluence** using Docker and Docker Compose.  
It prepares system directories, configures environment files, initializes Confluence, deploys supporting services, and helps with activation through the Atlassian agent.

The role also waits for Confluence's health status and guides you through retrieving and applying the server ID.

---

## Features

- Installs required Python packages for Docker management.
- Creates Docker networks for web and app layers.
- Prepares service directories and agent directory.
- Deploys Confluence with Docker Compose.
- Waits for container health check to pass.
- Guides user through server ID activation.
- Executes Atlassian agent inside Confluence container.
- Extracts the generated license and prints it on screen.

---

## Variables

### Default Variables

```yaml
DOMAIN: x
subdomain: x
project_dir: x
service_dir: x
restart_policy: x
CONFLUENCE_IMAGE_TAG: x
CONFLUENCE_HOSTNAME: x
DATA_PATH: x

confluence_email: x
company: x
service_name: x

CONFLUENCE_JVM_MINIMUM_MEMORY: x
CONFLUENCE_JVM_MAXIMUM_MEMORY: x

service_subdirs:
  - x

hostname_postgres: x

# secret vars
CONFLUENCE_DB_NAME: x
CONFLUENCE_DB_USER: x
CONFLUENCE_DB_PASSWORD: x
```
