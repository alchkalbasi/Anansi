<p><img src="./hero-logo.png" alt="Homer logo" title="homer" align="right" height="60" /></p>

# HOMER & Heplify Monitoring Stack

This project provides a complete SIP and RTCP monitoring solution using the **HOMER 7+** stack. It captures traffic from remote PBX/Switches using **heplify-agent** and centralizes it in a Dockerized **heplify-server**.

---

## 1. heplify-server (Capture Infrastructure)

The server is deployed via Docker Compose. It manages the storage of SIP packets into MariaDB and provides a metrics endpoint for monitoring.

## 2. heplify-agent (PBX / Switch Side)

The agent sits on the PBX/Switch, clones SIP/RTCP traffic, and sends it to the server via the HEP protocol. This is deployed manually as a binary for systems without Docker.

## 3. Observability & Dashboarding

### Prometheus Configuration

Add the following job to your prometheus.yml to scrape the capture server:

```YAML
scrape_configs:
  - job_name: 'heplify-server'
    metrics_path: /metrics
    static_configs:
      - targets: ['heplify-server:9096']
        labels:
          target: 'homer'
```
