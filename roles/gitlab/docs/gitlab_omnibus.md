# Gitlab Omnibus

GitLab Omnibus is the standard, most popular, and officially recommended(for under 3000 users) method for installing and managing a self-hosted instance of GitLab on Linux distributions.
It is a single, self-contained installation package (provided as a .deb or .rpm file) that bundles the GitLab application along with almost all the background services and dependencies required to run it.

<p><img src="../images/gitlab-omnibus.svg" alt="gitlab omnibus" title="gitlab omnibus" /></p>

## 1- Bundled Dependencies
Running a complex application like GitLab requires many different pieces of software to work together. Instead of making us install and configure each one manually, the Omnibus package includes them all. These bundled components include:

    - PostgreSQL (Database)
    - Redis (In-memory data structure store/cache)
    - Nginx (Web server)
    - Puma (Ruby web server)
    - Sidekiq (Background job processor)
    - Prometheus & Grafana (Monitoring and metrics)
    - Let’s Encrypt (For automatic SSL certificates)

## 2- Simplified Configuration

With Omnibus, we don’t need to configure Nginx, PostgreSQL, and Redis in their individual configuration files. Instead, GitLab provides a single, centralized configuration file located at **/etc/gitlab/gitlab.rb**.
Whenever we make a change to this file, we run a single command (**sudo gitlab-ctl reconfigure**), and GitLab automatically translates your settings to all the underlying services.

## 3- Easy Management

Omnibus provides a command-line tool called **gitlab-ctl**. This tool allows us to easily manage the entire GitLab stack. For example:

    - gitlab-ctl start / stop / restart (to manage all services at once)
    - gitlab-ctl tail (to view logs for all services)
    - gitlab-ctl status (to check the health of the components)

## 4- Simplified Upgrades

Because everything is packaged together, upgrading GitLab is usually as simple as updating the package via our OS package manager (e.g., apt-get upgrade gitlab-ee or yum update gitlab-ee). The Omnibus package handles migrating the database and updating the bundled software automatically.

---

#### **Notes**

- I choose SPOOF(Single Point Of Failur) for a gitlab with under 3000 users but for above 3000 users, I choose HA(High Availability) method.

- We have 4 main directories:

    - "/var/opt/gitlab" ---> application data's
    - "/etc/gitlab" ---> configs
    - "/var/log/gitlab" ---> logs
    - "/vat/opt/gitlab/backup" ---> backups

- Also we have some external url. For example:

    - Gitlab external-url  
    - Registery external-url
    - Mattermost external-url
    - Pages external-url