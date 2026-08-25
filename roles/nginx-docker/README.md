# NGINX Ansible Role

This role sets up an NGINX Docker container as part of a LEMP(Linux, Nginx, Mysql, and Python) stack, with custom configuration, read-only mounted volumes, and Docker networking.

---

## What It Does

* Creates the configuration directory:

  * `/etc/nginx/sites-available/lemp`
* Copies an NGINX config template (`nginx.conf.j2`) to the config path
* Runs an `nginx:{{ NGINX_VERSION }}` Docker container with:

  * Port mapping (`{{ NGINX_PORT }}:80`)
  * Read-only volume mount
  * Docker network connection (`{{ NETWORK }}`)

---

## Variables

Define in your playbook or inventory:

```yaml
PATH: /etc/nginx/sites-available/lemp
NGINX_VERSION: latest
NGINX_PORT: 2380
NETWORK: lempnet
```

---

## Usage

In your playbook:

```yaml
- hosts: localhost
  become: yes
  vars:
    PATH: /etc/nginx/sites-available/lemp
    NGINX_VERSION: latest
    NGINX_PORT: 2380
    NETWORK: lempnet
  roles:
    - nginx
```

Run:

```bash
ansible-playbook playbook.yml
```

---

## Tags

* `nginx-dir`
* `nginx-templates`
* `nginx-run`

Run specific tags with:

```bash
ansible-playbook playbook.yml --tags nginx-run
```