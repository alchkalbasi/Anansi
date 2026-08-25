# GitLab Administration Tools

## GitLab Upgrade Path Tool
**Link:** [GitLab Upgrade Path Generator](https://gitlab-com.gitlab.io/support/toolbox/upgrade-path/)

Upgrading a self-managed GitLab instance is rarely as simple as jumping straight to the latest release. Skipping specific minor or major versions can lead to severe database corruption. 

**Why we use this:**
* **Database Migrations:** GitLab runs background migrations that must completely finish before you can upgrade to the next version. 
* **Safe Stepping Stones:** This tool calculates the exact, safe, version-by-version path you must follow from our current version to our target version.
* **Prevents Data Loss:** Ensuring we hit every required "mandatory upgrade stop" guarantees we do not lose migrations or break the instance.
