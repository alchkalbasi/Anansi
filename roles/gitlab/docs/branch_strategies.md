# GitLab Branch Strategies & Workflow Best Practices

This document describes **production‑grade Git branching strategies and workflows** for teams using GitLab.  
It covers recommended models, when to use them, and best practices for maintaining a stable, scalable development process.

---

# Core Concepts

Before choosing a branching strategy, it's important to understand a few core Git concepts.

### Branch
A branch represents an independent line of development.

### Merge
Combines changes from one branch into another.

### Rebase
Rewrites commit history to apply commits on top of another base branch.

### Merge Request (MR)
In GitLab, a **Merge Request** is the process used to review, discuss, test, and approve code before merging it into a target branch.

### Protected Branch
A branch that restricts direct pushes and requires merge requests, approvals, and passing pipelines.

Production branches should **always be protected**.

---

# Common GitLab Branching Strategies

Different teams and projects require different workflows. The following strategies are widely used in production environments.

---

## 1. GitFlow

GitFlow is a **structured branching strategy designed for **release‑based** software development**.

It works well for large teams and projects with scheduled releases.

### Main Branches

#### main (or master)
- Production-ready code
- Always stable
- Every commit should represent a production release

#### develop
- Integration branch for features
- All completed features are merged here

---

### Supporting Branches

#### feature/*
Used for developing new features.

Example:

feature/payment-api  
feature/login-improvement

Workflow:

develop → feature branch → develop

Steps:

1. Create branch from `develop`
2. Implement feature
3. Open merge request
4. Run CI pipeline
5. Merge back into `develop`

---

#### release/*
Used for preparing production releases.

Example:

release/v1.4.0

Purpose:

- final testing
- documentation updates
- minor bug fixes

Workflow:

develop → release → main

After release:

release → main  
release → develop

---

#### hotfix/*
Used for urgent production fixes.

Example:

hotfix/security-patch

Workflow:

main → hotfix → main

Then merged back into:

develop

---

## 2. GitHub Flow / Simple Flow

This is a **lightweight workflow optimized for continuous delivery**.

Only one long‑lived branch exists:

main

All work happens in short‑lived branches.

### Workflow

1. Create feature branch from main
2. Commit changes
3. Open Merge Request
4. Run pipeline
5. Code review
6. Merge into main
7. Deploy

Example:

main → feature/login → main

---

## 3. GitLab Flow

GitLab Flow combines **GitFlow structure with environment-based deployment workflows**.

It introduces environment branches.

Example environments:

production  
staging  
pre-production

### Example Flow

feature → main → staging → production

or

feature → main → production

### Example Branch Structure

main  
staging  
production  
feature/*  
bugfix/*

### Workflow

1. Developer creates feature branch
2. Feature merged into `main`
3. CI deploys to staging
4. After validation → merge to production

---

## 4. Trunk-Based Development

Trunk-based development focuses on **very short-lived branches and frequent merges**.

Main branch is called:

main  
or trunk

Branches live for **hours or a few days at most**.

### Workflow

main → short feature branch → main

Key rules:

- small commits
- frequent merges
- feature flags for incomplete work

---

# Recommended Branch Naming Convention

feature/<name>  
bugfix/<name>  
hotfix/<name>  
release/<version>  
chore/<task>  
docs/<change>  
refactor/<component>

Examples:

feature/payment-service  
bugfix/login-timeout  
release/v2.1.0  
hotfix/security-token

---

# Branch Protection Best Practices

Production branches should always be protected.

Recommended protection for:

main  
production  
release/*

Enable:

- no direct pushes
- merge request required
- pipeline must pass
- required approvals
- signed commits (optional)

---

# Merge Request Best Practices

Recommended rules:

- pipeline must pass
- at least 1–2 reviewers
- squash commits before merge
- descriptive MR title
- link issue/ticket
- keep MRs small

Example MR title:

feat: add payment retry mechanism

---

# Commit Message Convention

Format:

type(scope): message

Types:

feat  
fix  
docs  
refactor  
test  
chore  
ci

Examples:

feat(auth): add oauth login  
fix(api): handle timeout error  
docs(readme): update setup instructions

---

# CI/CD Integration Best Practices

Example pipeline flow:

feature branch → run tests  
main → build + integration tests  
release → staging deployment  
production → production deployment

---

# Recommended Strategy by Team Size

Small Team (1–5 developers)

GitHub Flow or Trunk-Based Development

Medium Team (5–20 developers)

GitLab Flow

Large Enterprise Teams

GitFlow or GitLab Flow with environments

---

# Additional Best Practices

- Keep branches short-lived
- Use feature flags
- Automate testing and deployments
- Monitor pipeline health
- Keep main always deployable

---

# Example Production Workflow

main  
production  
feature/*  
bugfix/*  
hotfix/*

Process:

feature → MR → main  
main → automatic deploy → staging  
staging validated → merge → production

---