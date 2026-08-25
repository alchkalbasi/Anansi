# MySQL Ansible Role

This role sets up a MySQL Docker container with custom configuration, persistent storage, and networking.

---

## What It Does

* Creates host directories:

  * `/var/mysql/backups`
  * `/etc/mysql/conf.d`
  * `/var/mysql/lib`
* Copies MySQL config templates (`*.cnf.j2`) to `/etc/mysql/conf.d`
* Runs a `mysql:{{ MYSQL_VERSION }}` Docker container with:

  * Custom environment vars
  * Port mapping (`{{ MYSQL_PORT }}:3306`)
  * Mounted volumes
  * Docker network

---

## Variables

Define in your playbook or inventory:

```yaml
MYSQL_VERSION: "8.0"
MYSQL_ROOT_PASSWORD: "root"
MYSQL_DATABASE: "mydb"
MYSQL_PORT: "3306"
NETWORK: "mysql_net"
```

---

## Usage

In your playbook:

```yaml
- hosts: localhost
  become: yes
  vars:
    MYSQL_VERSION: "8.0"
    MYSQL_ROOT_PASSWORD: "root"
    MYSQL_DATABASE: "mydb"
    MYSQL_PORT: "3306"
    NETWORK: "mysql_net"
  roles:
    - mysql
```

Run:

```bash
ansible-playbook playbook.yml
```

---

## Tags

* `mysql-dirs`
* `mysql-templates`
* `mysql-run`

Run specific tags with:

```bash
ansible-playbook playbook.yml --tags mysql-run
```

