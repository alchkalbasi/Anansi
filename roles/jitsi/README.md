# Jitsi Deployment with Ansible

This Ansible role deploys a full Jitsi stack including:

- **Jitsi Web (Web UI)**
- **Jitsi Videobridge (JVB)**
- **Prosody (XMPP Server)**
- **Jicofo (Jitsi Conference Focus)**

All components are deployed using a `docker-compose` setup, behind a reverse proxy.

---

## Prerequisites

- Docker and Docker Compose installed on the target host.
- Ansible installed on the control machine.
- Domain name pointed to your server (e.g., `meet.example.com`).
- Traefik configured for reverse proxy (optional, if you want Traefik).
- Ports 80 and 443 open for HTTP/HTTPS reverse-proxy.

---

## Deployment overview

This role will set up the Jitsi platform running in Docker containers, routing requests through Traefik. It configures the necessary services and networking, making it easy to deploy a scalable video conferencing solution.

---

## Post-deployment steps

### Creating the Jitsi Prosody admin user

Once the containers are up and running, create an admin user to manage the XMPP server:

```bash
docker exec -it jitsi-prosody-1 prosodyctl --config /config/prosody.cfg.lua register admin $XMPP_DOMAIN [PASSWORD]
```

- Replace `$XMPP_DOMAIN` with your configured domain (e.g., `meet.example.com`).
- Replace `[PASSWORD]` with a secure password for the admin user.

---

## Example NGINX reverse proxy configuration

If you are not using Traefik and instead opting for NGINX as the reverse proxy, use this example configuration to proxy traffic correctly to your Jitsi service running locally on port 8000. This configuration wrote for a server behind a CDN:

```nginx
server {
    listen 80;
    server_name $URL;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $remote_addr;
    }

    location /xmpp-websocket {
        proxy_pass http://127.0.0.1:8000/xmpp-websocket;
        proxy_http_version 1.1;

        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $remote_addr;
    }

    location /colibri-ws {
        proxy_pass http://127.0.0.1:8000/colibri-ws;
        proxy_http_version 1.1;

        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $remote_addr;
    }
}
```

- This setup handles standard HTTP requests and WebSocket upgrades necessary for Jitsi’s XMPP websocket and Colibri communication.
- Make sure your NGINX has the necessary modules enabled for proxying WebSocket traffic.

---