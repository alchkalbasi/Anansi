# Python Web Server Ansible Role

This role sets up a lightweight Python HTTP server inside a Docker container. It creates the necessary directory structure, injects a custom HTML template, and launches the container with network and volume configurations.

---

## What It Does

* Creates a host directory:

  * `/home/html`
* Copies an HTML template (`index.html.j2`) to the target directory as `index.html`
* Runs a `python:{{ python_version }}` Docker container with:

  * Port mapping (`{{ publish_port }}:{{ target_port }}`)
  * Mounted volume (read-only)
  * Custom working directory
  * Command to run a simple HTTP server
  * Docker network

---

## Variables

Define in your playbook or inventory:

```yaml
dir_path: /home/html
template: index.html.j2
project_name: index.html
container_name: html-server
python_version: latest
publish_port: 8000
target_port: 8000
network: lempnet
working_dir: /home/html
```

---

## Usage

In your playbook:

```yaml
- hosts: localhost
  become: yes
  vars:
    dir_path: /home/html
    template: index.html.j2
    project_name: index.html
    container_name: html-server
    python_version: latest
    publish_port: 8000
    target_port: 8000
    network: lempnet
    working_dir: /home/html
  roles:
    - python-web
```

Run:

```bash
ansible-playbook playbook.yml
```

---

## Tags

* `python-dir` — Creates the directory
* `project-templates` — Copies the HTML file
* `python-run` — Runs the Python container

Run specific tags with:

```bash
ansible-playbook playbook.yml --tags python-run
```