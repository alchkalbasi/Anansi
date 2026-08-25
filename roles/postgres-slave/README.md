<p><img src="./postgresql-logo.svg" alt="postgres logo" title="postgres" align="right" height="60" /></p>

# PostgreSQL Master-Slave Replication: Slave Role

This Ansible role deploys a **PostgreSQL Slave (Standby)** instance. It automates the initial data synchronization from the Master using `pg_basebackup` and maintains a streaming replication state.

---

## Overview

The Slave role is responsible for maintaining a read-only copy of the Master database. 

* **Automated Provisioning**: Uses a temporary Docker container to perform `pg_basebackup` if the data directory is empty.
* **Stream Synchronization**: Automatically creates `standby.signal` and configures connection parameters to the Master.
* **Continuous Monitoring**: Includes a sidecar `postgres-exporter` for tracking replication lag and health.
* **Idempotency**: Checks for `PG_VERSION` to ensure synchronization only happens once, preventing accidental data overwrites.



---

## Deployment

### Prerequisites

* **A Running Master**: The Master role must be deployed and the `postgres_replication_user` must be active.
* **Network Connectivity**: Port `5432` must be reachable from the Slave to the Master IP.
* **Docker CE** and **Docker Compose Plugin** installed on the target host.

### Variables

All variables in `defaults/main.yml` are **example variables**. You should define your actual environment variables in `host_vars`, `group_vars`, or your CI/CD secrets.

---

## File Structure

The role manages the following structure in `{{ service_dir }}`:
* `pgdata/`: The replicated data directory (initially populated by `pg_basebackup`).
* `postgresql.conf`: Slave-specific configuration (e.g., `hot_standby = on`).
* `pg_hba.conf`: Authentication rules for the Slave instance.
* `compose.yml`: Docker Compose file defining the Slave and Exporter services.

---

## Technical Workflow

1. **Environment Check**: Verifies Docker and Compose availability.
2. **Replication Check**: Looks for existing data. If missing, it triggers the `replication-sync` task.
3. **Data Sync**: Runs a transient `postgres-basebackup` container to pull a full snapshot from the Master.
4. **Configuration**: Templates the `postgresql.conf` and `.env` files.
5. **Deployment**: Launches the Slave container in `hot_standby` mode.

---

## Maintainer

**Name:** [Ali Kalbasi]  
**Email:** ali99kalbasi82@gmail.com