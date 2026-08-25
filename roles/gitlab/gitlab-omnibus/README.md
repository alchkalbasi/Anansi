<p><img src="../images/gitlab-logo.svg" alt="gitlab logo" title="GitLab" align="right" height="70" /></p>

# Ansible Role: Gitlab-Omnibus Deployment

## Description

Deploy [GitLab-Omnibus](../docs/gitlab_omnibus.md) using Ansible with Docker and Docker Compose. This role includes setup of the GitLab-Omnibus service, backup configuration, and automated cron jobs for regular backups. Certificates and networking are handled for secure deployments.

This role can be used for any GitLab instance with the SPOOF (Single Point of Failure) method, on a server with custom subdomains and configuration.

## Requirements

- A server with at least a 4‑core CPU and 8 GB of RAM.
- A server with sufficient storage.
- A hardened server is preferred.
- Docker Engine installed on the target host.
- Docker Compose V2 CLI plugin (the role uses the docker_compose_v2 module).
- At least two subdomains.
- A healthy and ready Traefik service.
- An S3-compatible service such as MinIO, with two prepared buckets for backups and registry images.

## Gitlab-Omnibus Setup

### Gitlab Configuration

GitLab is configured through environment variables in the Docker Compose file.

#### Gitlab main url

  ```
  # Gitlab external url
  external_url 'https://${GITLAB_DOMAIN}'
  ```
- ${GITLAB_DOMAIN} is composed of the main domain and the GitLab subdomain.

#### Initial root(admin) password
  ```
  # Gitlab Root Password
  gitlab_rails['initial_root_password'] = "${GITLAB_ROOT_PASS}"
  gitlab_rails['display_initial_root_password'] = false
  gitlab_rails['store_initial_root_password'] = false
  ```
- GitLab takes the root password from variables and is configured not to display the password in logs and not to store it in the default path. 

#### Nginx configuration
  - These are internal Nginx configurations:
  ```
  # Gitlab Nginx Config
  nginx['enable'] = true
  nginx['client_max_body_size'] = '${GITLAB_NGINX_MAX_BODY}'
  nginx['gzip_enabled'] = true
  nginx['listen_port'] = 80
  nginx['listen_https'] = false
  nginx['proxy_cache'] = 'gitlab'
  nginx['http2_enabled'] = true
  nginx['proxy_set_headers'] = {
    "Host" => "$$http_host",
    "X-Real-IP" => "$$remote_addr",
    "X-Forwarded-For" => "$$proxy_add_x_forwarded_for",
    "X-Forwarded-Proto" => "https",
    "X-Forwarded-Ssl" => "on"
  }
  ```
- HTTPS is disabled because Traefik handles TLS termination.
- Client max body size, gzip, and HTTP/2 are configured.
- Required proxy headers are set.

#### SMTP configuration
  ```
  # GitLab smtp server settings
  gitlab_rails['smtp_enable'] = true
  gitlab_rails['smtp_address'] = "${SMTP_ADDRESS}"
  gitlab_rails['smtp_port'] = ${SMTP_PORT}
  gitlab_rails['smtp_user_name'] = "${SMTP_USERNAME}"
  gitlab_rails['smtp_password'] = "${SMTP_PASSWORD}"
  gitlab_rails['smtp_domain'] = "${SMTP_DOMAIN}"
  gitlab_rails['smtp_authentication'] = "login"
  gitlab_rails['smtp_enable_starttls_auto'] = true
  gitlab_rails['smtp_tls'] = false
  gitlab_rails['smtp_openssl_verify_mode'] = 'peer'
  ```

#### Configure a failed authentication
- Similar to Fail2ban:
  ```
  # Gitlab ban authentication failed
  gitlab_rails['rack_attack_git_basic_auth'] = {
    'enabled' => true,
    'ip_whitelist' => ["127.0.0.1"],
    'maxretry' => 10,
    'findtime' => 60,
    'bantime' => 3600
  }
  ```

#### Backup configuration
- Default backup command configurations:
  ```
  # Gitlab Backup Settings
  gitlab_rails['manage_backup_path'] = true
  gitlab_rails['backup_path'] = "/var/opt/gitlab/backups"
  gitlab_rails['backup_archive_permissions'] = 0600
  gitlab_rails['backup_keep_time'] = ${GITLAB_BACKUP_KEEP_TIME}
  gitlab_rails['env'] = {
      "SKIP" => "registry"
  }
  gitlab_rails['backup_upload_connection'] = {
    'provider' => 'AWS',
    'region' => 'eu-west-1',
    'aws_access_key_id' => '${GITLAB_S3_ACCESS_KEY}',
    'aws_secret_access_key' => '${GITLAB_S3_SECRET_KEY}',
    'endpoint' => '${GITLAB_S3_ENDPOINT}',
    'path_style' => true
  }
  gitlab_rails['backup_upload_remote_directory'] = '${GITLAB_S3_BUCKET}'
  gitlab_rails['backup_multipart_chunk_size'] = 104857600
  ```
- Backups are stored locally and uploaded to an S3 bucket.

#### Gitlab registry configuration

- The registry requires a domain, an S3 bucket, and Nginx configurations:
  ```
  # Settings used by GitLab registry
  registry_external_url 'https://${REGISTRY_DOMAIN}'
  registry_nginx['enable'] = true
  registry_nginx['client_max_body_size'] = '${GITLAB_REG_MAX_BODY}'
  registry_nginx['listen_port'] = 5001
  registry_nginx['listen_https'] = false
  registry_nginx['proxy_set_headers'] = {
    "Host" => "$$http_host",
    "X-Real-IP" => "$$remote_addr",
    "X-Forwarded-For" => "$$proxy_add_x_forwarded_for",
    "X-Forwarded-Proto" => "https",
    "X-Forwarded-Ssl" => "on"
  }
  registry['storage'] = {
      's3' => {
        'accesskey' => '${GITLAB_S3_ACCESS_KEY}',
        'secretkey' => '${GITLAB_S3_SECRET_KEY}',
        'bucket' => '${GITLAB_REGISTERY_S3_BUCKET}',
        'region' => 'us-east-1',
        'regionendpoint' => '${GITLAB_S3_ENDPOINT}'
      }
    }
  ```
- HTTPS is disabled because Traefik is used as the main reverse proxy.

#### Disable unused service
- To reduce unnecessary resource usage.
  ```
  # Gitlab disable unused services
  node_exporter['enable'] = false
  redis_exporter['enable'] = false
  postgres_exporter['enable'] = false
  pgbouncer_exporter['enable'] = false
  gitlab_exporter['enable'] = false
  letsencrypt['enable'] = false
  prometheus['enable'] = false
  monitoring_role['enable'] = false
  alertmanager['enable'] = false
  ```

### Traefik labels

#### Global
```
- "traefik.enable=true"
```

#### Gitlab
```
- "traefik.http.routers.http-git.rule=Host(`${GITLAB_DOMAIN}`)"
- "traefik.http.routers.http-git.entrypoints=web"
- "traefik.http.routers.git.rule=Host(`${GITLAB_DOMAIN}`)"
- "traefik.http.routers.git.entrypoints=web-secure"
- "traefik.http.routers.git.tls=true"
- "traefik.http.routers.git.tls.certresolver=le"
- "traefik.http.routers.git.service=git"
- "traefik.http.services.git.loadBalancer.server.port=80"
```

#### Registery
```
- "traefik.http.routers.http-reg.rule=Host(`${REGISTRY_DOMAIN}`)"
- "traefik.http.routers.http-reg.entrypoints=web"
- "traefik.http.routers.reg.rule=Host(`${REGISTRY_DOMAIN}`)"
- "traefik.http.routers.reg.entrypoints=web-secure"
- "traefik.http.routers.reg.tls=true"
- "traefik.http.routers.reg.tls.certresolver=le"
- "traefik.http.routers.reg.service=reg"
- "traefik.http.services.reg.loadBalancer.server.port=5001"
```

## GitLab Backup

The backup process is managed using two main YAML files:

- `backup.yml`
- `cron.yml`

### Backup Strategy

The backup strategy covers both **GitLab data** and **GitLab configuration files**.

1. **GitLab Data Backup**  
   GitLab data is backed up using the built-in GitLab command:
    - `gitlab-backup create`

2. **Configuration Backup**  
   Important configuration files are backed up using a custom script. These include:
   - `gitlab.rb`
   - `gitlab-secrets.json`

### Storage

Both data and configuration backups are stored in:
- **S3** for remote storage
- **Local storage** on the backup system

### YAML Files

#### `backup.yml`
Creates the backup directory and generates the backup script used for backing up GitLab configuration files.

#### `cron.yml`
Creates two cron jobs:
- One job runs the GitLab CLI command to back up GitLab data.
- The other job executes the custom script to back up GitLab configuration files.

### Backup Script

This script creates a backup of the GitLab configuration data stored in the Docker volume. It archives the configuration files, encrypts the backup using **GPG (AES‑256)**, and uploads the encrypted file to an **S3-compatible object storage**.

The process includes the following steps:

- Archive GitLab configuration files from the Docker volume.
- Store the archive in the local backup directory.
- Encrypt the backup using a passphrase.
- Ensure the MinIO client (`mc`) is installed and configured.
- Upload the encrypted backup to the configured S3 bucket.
- Remove the uploaded encrypted file from the local system after successful transfer.

This ensures that GitLab configuration backups are **securely stored both locally and in remote object storage**.
