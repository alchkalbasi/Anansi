# GitLab Backup & Restoration Guide

This document outlines the standard operating procedures, best practices, and strategies for backing up and restoring a self-managed GitLab instance. 

> **⚠️ CRITICAL WARNING:** The standard GitLab backup command does **NOT** backup your configuration files or SSH keys. If you lose your `gitlab-secrets.json` file, your database backup becomes effectively useless, as all two-factor authentication (2FA), CI/CD variables, and encrypted tokens will be locked forever.

<p><img src="../images/gitlab-backup.svg" alt="gitlab backup" title="gitlab backup" /></p>

## Table of Contents
1. [What is Backed Up vs. Excluded](#1-what-is-backed-up-vs-excluded)
2. [Manual Backup Procedures](#2-manual-backup-procedures)
3. [The Best Backup Strategies](#3-the-best-backup-strategies)
4. [Automating Backups (Cron & Object Storage)](#4-automating-backups)
5. [Restoration Procedure](#5-restoration-procedure)

---

## 1. What is Backed Up vs. Excluded

### Included in standard backup (`gitlab-backup create`):
* Database (PostgreSQL)
* Git repositories
* Container Registry images
* GitLab Pages
* Attachments, avatars, and CI/CD job artifacts
* LFS objects

### EXCLUDED (Must be backed up manually):
* `/etc/gitlab/gitlab.rb` (GitLab configuration)
* `/etc/gitlab/gitlab-secrets.json` (Database encryption keys - **CRITICAL**)
* TLS/SSL Certificates (Usually in `/etc/gitlab/ssl/`)
* SSH Host Keys (`/etc/ssh/ssh_host_*`)

---

## 2. Manual Backup Procedures

### Backing up GitLab Data
To trigger a manual backup on an Omnibus Linux installation:
```bash
sudo gitlab-backup create
```
*Note: Backups are stored in `/var/opt/gitlab/backups/` by default.*

### Backing up Configuration & Secrets
Create a secure archive of your configuration:
```bash
sudo sh -c 'umask 0077; tar cfz /secret/backup/path/gitlab-config-backup-$(date "+%s").tar.gz -C / etc/gitlab'
```

---

## 3. The Best Backup Strategies

To ensure absolute resilience, implement the following strategies:

### A. The $3-2-1$ Backup Rule
* **$3$** Copies of your data (1 production copy + 2 backup copies).
* **$2$** Different storage media types (e.g., Local storage + Cloud Object Storage).
* **$1$** Offsite copy (e.g., AWS S3, GCP Cloud Storage, or an offsite NAS).

### B. Cloud Object Storage Integration (Recommended)
Instead of keeping backups on the local disk (which is dangerous if the server dies), configure GitLab to push backups directly to Object Storage (S3, MinIO, Azure Blob). 

### C. Separate Configuration Backups
Never store `/etc/gitlab` backups in the exact same location as your application backups. If an attacker gains access to your backup bucket, having both the database and the `gitlab-secrets.json` file compromises all encrypted data.

### D. File System Snapshots (For Massive Instances)
If your GitLab instance is very large ($>100\text{ GB}$ of Git data), running `gitlab-backup create` can take hours and impact performance. 
* **Strategy:** Use underlying storage snapshots (AWS EBS snapshots, ZFS, or LVM snapshots) combined with PostgreSQL streaming replication instead of the standard tarball backup.

### E. Regular Restoration Drills (Game Days)
**A backup is not a backup until it has been successfully restored.**
Schedule a monthly or quarterly "Game Day" where you restore your GitLab backup to a staging server to verify data integrity.

---

## 4. Automating Backups

### Step 1: Configure Object Storage (`/etc/gitlab/gitlab.rb`)
Add your S3/Cloud credentials to push backups offsite automatically:

```ruby
gitlab_rails['backup_upload_connection'] = {
  'provider' => 'AWS',
  'region' => 'us-east-1',
  'aws_access_key_id' => 'YOUR_ACCESS_KEY',
  'aws_secret_access_key' => 'YOUR_SECRET_KEY'
}
gitlab_rails['backup_upload_remote_directory'] = 'my-gitlab-backup-bucket'
# Keep local backups for 3 days (in seconds: 3 * 24 * 3600 = 259200)
gitlab_rails['backup_keep_time'] = 259200
```
Run `sudo gitlab-ctl reconfigure` after saving.

### Step 2: Automate with Cron
Add a cron job to run daily at 2:00 AM. 

```bash
sudo crontab -e
```
Add the following lines (the `CRON=1` flag suppresses progress output):
```cron
# Daily GitLab Data Backup
0 2 * * * /opt/gitlab/bin/gitlab-backup create CRON=1

# Daily Configuration Backup
0 3 * * * umask 0077; tar cfz /path/to/secure/storage/gitlab-config-$(date +\%Y-\%m-\%d).tar.gz -C / etc/gitlab
```

---

## 5. Restoration Procedure

> **Note:** You can only restore a backup to the **exact same version** of GitLab that the backup was created on (e.g., You cannot restore a `16.2.0` backup onto a `16.5.0` server).

### Step 1: Restore Configuration
Move your backed-up `gitlab.rb` and `gitlab-secrets.json` into `/etc/gitlab/` and reconfigure:
```bash
sudo cp gitlab.rb /etc/gitlab/
sudo cp gitlab-secrets.json /etc/gitlab/
sudo gitlab-ctl reconfigure
```

### Step 2: Stop Services connected to the Database
```bash
sudo gitlab-ctl stop puma
sudo gitlab-ctl stop sidekiq
```
*Verify they are down:* `sudo gitlab-ctl status`

### Step 3: Run the Restore Command
Ensure your backup `.tar` file is in `/var/opt/gitlab/backups/`. Look at the filename, e.g., `1690000000_2023_07_22_16.2.0_gitlab_backup.tar`. 

The `BACKUP` variable is the filename *up to* `_gitlab_backup.tar`.

```bash
sudo gitlab-backup restore BACKUP=1690000000_2023_07_22_16.2.0
```

### Step 4: Restart and Check
```bash
sudo gitlab-ctl restart
sudo gitlab-rake gitlab:check SANITIZE=true
```

---