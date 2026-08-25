<p><img src="../images/gitlab-logo.svg" alt="gitlab logo" title="gitlab" align="right" height="70" /></p>

# Gitlab Components

Gitlab is an all-in-one application but it is composed of several independent services and components that work together. We can categorized these services in 5 groups by their roles.

<p><img src="../images/gitlab-components.svg" alt="gitlab components" title="gitlab components" /></p>

## 1- Web and Application Servers

These components handle incoming requests, run the core GitLab application, and serve it to users.

### Nginx

This is the “front door” of GitLab. It is a high-performance web server and reverse proxy. It terminates SSL/TLS (handles HTTPS), manages static assets, and routes incoming traffic to the appropriate internal GitLab components (like Workhorse, Pages, or the Container Registry).

- I prefer to disable "SSL/TLS" in internal Nginx of Gitlab and use an external reverse-proxy like Traefik.

### GitLab Workhorse

Written in Go, Workhorse acts as an “smart” reverse proxy that sits directly in front of Puma. The Ruby on Rails framework (which GitLab is built on) is not efficient at handling long-running or large requests, like cloning a massive Git repository or uploading a large file. Workhorse intercepts these heavy requests, handles the file streaming or Git traffic itself, and only talks to Puma for authentication and authorization.

### Puma

This is the main web server that runs the core Ruby on Rails application. It handles user interface rendering, API requests, and business logic. Puma replaced the older “Unicorn” server because it is multi-threaded and consumes less memory.

## 2- Background Processing

GitLab needs to perform many tasks asynchronously.

### Sidekiq

This is a background job processor written in Ruby. When we click “Merge” on a Merge Request, trigger a CI/CD pipeline, or when GitLab needs to send an email notification, Puma pushes a job to Sidekiq. Sidekiq picks up these jobs from a queue and executes them in the background.

## 3- Data and State Storage

GitLab requires several different types of databases to store different types of data.

### Postgres

This is the primary relational database. It stores almost all of the application’s metadata: user accounts, issues, merge request discussions, repository metadata, CI/CD pipeline statuses, and project settings.

### Redis

This is an in-memory key-value data store. GitLab uses Redis for three main things:

	1- Caching frequently accessed data to speed up page loads.
	2- Storing user session data.
	3- Holding the queues of background jobs waiting to be processed by Sidekiq.

### Gitaly

**Gitaly** is the core service written in Go that handles all Git operations. In the past, GitLab instances accessed Git repositories directly via shared file systems (NFS). This caused major performance bottlenecks. Gitaly was introduced as an RPC (Remote Procedure Call) service. Now, whenever Puma or Workhorse needs to read or write to a Git repository, they ask Gitaly to do it.


## 4- CI/CD & DevOps Features

These components handle the actual building, testing, and deployment of code.

### GitLab Runner

This is an independent, lightweight agent written in Go that runs your CI/CD jobs. When a pipeline is triggered, GitLab hands the instructions (from our .gitlab-ci.yml file) to a Runner. The Runner executes the scripts (often inside Docker containers) and sends the logs and results back to the main GitLab application. Runners are usually(**Best-Practice**)  installed on separate servers to prevent CI jobs from consuming the main GitLab server’s resources and other problems.

### GitLab Pages

This is a simple HTTP server written in Go that serves static websites directly from a GitLab repository. When a CI/CD pipeline generates static HTML/CSS (like a Hugo, Jekyll, or React build), GitLab Pages hosts it so it can be viewed on the web.

### Container Registry

GitLab includes a fully integrated Docker container registry. This allows developers to build Docker images in their CI/CD pipelines and push them directly to GitLab for storage, similar to Docker Hub.

- We usually use a nexus or registery for our images, not both.

### KAS (GitLab Agent Server for Kubernetes)

This component enables secure, bi-directional communication between GitLab and our Kubernetes clusters. It allows GitLab to deploy applications to Kubernetes and monitor cluster health without needing to open firewall ports to the cluster.

## 5- Monitoring and Observability

GitLab ships with tools to monitor its own health.

### Prometheus

A time-series database that continuously scrapes metrics from Puma, Workhorse, Gitaly, PostgreSQL, and other components to track their health, CPU usage, memory, and error rates.

### Grafana

A visualization dashboard that reads the data from Prometheus and displays it in easy-to-read graphs and charts, helping administrators monitor the GitLab instance.

### Exporters

Many exporter services that scrape the metrics for prometheus or any other TSDB's.

---

#### **Notes**

- We usually disable unnecessary services to save resources.
- I usually disable:
	- prometheus
	- grafana
	- pages
	- and some of the exporters





