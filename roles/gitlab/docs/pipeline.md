# GitLab Pipelines

A GitLab pipeline is a set of automated processes (jobs) organized into stages. Pipelines are used to build, test, and deploy applications automatically whenever changes are made to the repository.

## Pipeline Types

GitLab supports several pipeline architectures depending on how jobs and dependencies are structured.

### Basic Pipeline
A simple pipeline that runs jobs sequentially in stages such as:

stage1 → stage2 → stage3

Each stage starts only after the previous stage completes successfully.

### DAG Pipeline
DAG (Directed Acyclic Graph) pipelines allow jobs to run based on dependencies rather than strict stage order.  
This enables jobs to run in parallel when possible, reducing overall pipeline time.

### Merge Request Pipeline
A pipeline that runs automatically when a merge request is created or updated.  
It is typically used to validate code before merging it into the target branch.

### Parent–Child Pipeline
A pipeline that triggers another pipeline within the same repository.  
This helps break large pipelines into smaller, more manageable pieces.

### Multi‑Project Pipeline
A pipeline that triggers a pipeline in a different repository.  
Useful when multiple repositories are part of the same system.

### Scheduled Pipeline
A pipeline that runs automatically based on a defined schedule (e.g., nightly builds, periodic tests).

## Pipeline Trigger Types

Pipelines can be triggered in several ways:

- API trigger
- Manual trigger
- On tag creation
- On commit or push
- Scheduled trigger
- Merge request events

## Pipeline Efficiency

Pipeline efficiency focuses on reducing execution time and resource usage.

GitLab provides tools such as the **GitLab CI Pipeline Exporter** to help monitor pipeline performance.

Common techniques for improving pipeline efficiency include:

1. **Pipeline Analysis**  
   Identify slow jobs and bottlenecks.

2. **Pipeline Monitoring**  
   Track pipeline metrics and performance over time.

3. **Pipeline Exporter**  
   Export pipeline metrics for monitoring systems (e.g., Prometheus/Grafana).

4. **Fast-Fail Strategy**  
   Run quick validation jobs first so pipelines fail early if something is wrong.

5. **Caching**  
   Cache dependencies and build artifacts to avoid repeating expensive steps.

6. **Optimized Docker Images**  
   Use smaller and prebuilt images to reduce job startup time.


**Note:** Running jobs in parallel can significantly reduce pipeline duration.  
When possible, split independent tasks into multiple jobs so they can run simultaneously.

## Pipeline Jobs

Jobs are the smallest executable units in a GitLab pipeline.  
Each job performs a specific task such as building the project, running tests, or deploying an application.

Jobs are defined in the `.gitlab-ci.yml` file and executed by **GitLab Runners**.

### Job Characteristics

- **Isolated execution**  
  Each job runs in an isolated environment (usually a Docker container or a runner environment). Jobs do not share filesystem state by default.

- **Artifacts for sharing data**  
  Jobs can pass files to other jobs using **artifacts**. Artifacts are stored after a job finishes and can be downloaded or used by later jobs.

- **Parallel execution**  
  Jobs in the same stage run in parallel when runners are available. The number of jobs that can run simultaneously depends on the **runner concurrency configuration**.

- **Dependencies**  
  Jobs can explicitly depend on artifacts from earlier jobs using `dependencies` or `needs`.

- **Delayed jobs**  
  Jobs can be configured with a delay using `when: delayed` and `start_in`, which allows them to run after a specific time.

- **Manual jobs**  
  Some jobs require manual approval before execution, which is commonly used for deployment steps.

### Useful Job Keywords

Some commonly used job configuration options:

- `stage` – Defines the stage the job belongs to.
- `script` – Commands executed by the job.
- `image` – Docker image used to run the job.
- `artifacts` – Files passed to later jobs.
- `needs` – Allows jobs to start earlier by defining dependencies.
- `dependencies` – Specifies which job artifacts should be downloaded.
- `only` / `except` or `rules` – Controls when a job runs.
- `retry` – Automatically retries a failed job.
- `timeout` – Maximum time allowed for the job.
- `tags` – Selects which runners can execute the job.

### Job Statuses

A job can have several statuses during its lifecycle:

- **created** – Job has been created but not yet queued.
- **pending** – Waiting for a runner to pick it up.
- **running** – Currently executing.
- **success** – Completed successfully.
- **failed** – Execution finished with errors.
- **canceled** – Job was manually or automatically canceled.
- **skipped** – Job was skipped due to rules or conditions.
- **manual** – Waiting for a user to trigger it.
- **scheduled** – Waiting to run at a scheduled time.
- **warning** – Job completed with warnings (e.g., `allow_failure: true`).

