<p><img src="./postgresql-logo.svg" alt="postgres logo" title="postgres" align="right" height="60" /></p>

# PostgreSQL Master-Slave Replication: Master Role

This Ansible role deploys a **PostgreSQL Master** instance optimized for Streaming Replication. It includes an integrated **Postgres Exporter** for Prometheus monitoring and automated initialization of replication identities.

---

## Overview

The role sets up a Primary database node designed to accept replication connections from a standby node.

* **Custom Configuration**: Uses specific `postgresql.conf`, `pg_hba.conf`, and `init-replication.sql` templates.
* **Replication User**: Automatically creates a dedicated `postgresreplicationuser` during first boot.
* **Healthchecks**: Built-in Docker healthchecks using `pg_isready`.
* **Monitoring**: Sidecar container using `prometheuscommunity/postgres-exporter`.

---

## Deployment

### Prerequisites

* **Docker CE** and **Docker Compose Plugin** installed on the target host.
* The `community.docker` Ansible collection.

### Variables

All variables in `defaults/main.yml` are **example variables**. You should define your actual environment variables in `host_vars`, `group_vars`, or your CI/CD secrets.

---

## File Structure

The role manages the following structure in `{{ service_dir }}`:
* `pgdata/`: Physical database files.
* `init-db/`: Initialization SQL scripts (run only on first boot).
* `wal_archive/`: Directory for Write-Ahead Log archiving.
* `postgresql.conf`: Main configuration (overrides internal defaults).
* `pg_hba.conf`: Host-Based Authentication (the "Guest List").

---

## Maintainer

**Name:** [Ali Kalbasi]  
**Email:** ali99kalbasi82@gmail.com