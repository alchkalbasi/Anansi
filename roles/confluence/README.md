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
confluence_domain: x
confluence_subdomain: x
confluence_project_dir: x
confluence_service_dir: x
confluence_restart_policy: x
confluence_image_tag: x
confluence_hostname: x
confluence_data_path: x

confluence_email: x
confluence_company: x
confluence_service_name: x

confluence_jvm_minimum_memory: x
confluence_jvm_maximum_memory: x

confluence_service_subdirs:
  - x

confluence_postgres_hostname: x

# secret vars
confluence_db_name: x
confluence_db_user: x
confluence_db_password: x
```
