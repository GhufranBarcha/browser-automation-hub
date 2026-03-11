# Deployment Guide — Ubuntu VPS (Hostinger)

This guide deploys both the FastAPI backend and React frontend on a single Ubuntu VPS using Nginx as a reverse proxy.

## Requirements

- **Ubuntu 22.04 or 24.04** VPS with root access
- **4 GB+ RAM** (each browser task uses ~500MB; `MAX_CONCURRENCY=3` needs ~2GB for browsers alone)
- **2+ vCPUs** recommended

## Security Architecture

```
User Browser → Port 80/443 (Public) → Nginx
                                       │
                                       ├─ [Frontend Static Files]
                                       └─ [API Proxy] → Port 8000 (Private/Local)
```

**Key Security Features:**
- **Hidden Backend:** Port 8000 is restricted to `127.0.0.1`. It cannot be accessed directly from the internet.
- **Single Entry Point:** All traffic flows through Nginx.
- **Firewall Isolation:** We explicitly allow only HTTP (80) and HTTPS (443) traffic.

---

## Step 1: Install System Dependencies

```bash
# Update & upgrade
apt update && apt upgrade -y

# Python 3.12
apt install -y software-properties-common
add-apt-repository ppa:deadsnakes/ppa -y
apt update
apt install -y python3.12 python3.12-venv python3.12-dev

# Node.js 20
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt install -y nodejs

# Nginx, git, and build tools
apt install -y nginx git curl

# Firewall Setup (Crucial: ONLY expose Web Ports)
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw --force enable

# uv (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env
```

## Step 2: Upload / Clone the Project

**Option A — Git clone:**
```bash
cd /opt
git clone YOUR_REPO_URL browseruse-app
cd browseruse-app
```

**Option B — SCP from local machine:**
```bash
# Run from your local machine:
scp -r ./BrowserUse-jahaadbeckford root@YOUR_SERVER_IP:/opt/browseruse-app
```

## Step 3: Install Python Dependencies

```bash
cd /opt/browseruse-app

# Create venv and install all packages
uv venv .venv --python 3.12
source .venv/bin/activate
uv sync

# Install Playwright Chromium + its OS-level deps
playwright install --with-deps chromium
```

## Step 4: Configure Environment

```bash
cat > /opt/browseruse-app/.env << 'EOF'
ANTHROPIC_API_KEY=sk-ant-xxxxx-your-real-key
APP_LOGIN_EMAIL=admin@browseruse.com
APP_LOGIN_PASSWORD=YourStrongPassword!
SECRET_KEY=REPLACE_WITH_RANDOM_STRING
MAX_CONCURRENCY=2
LLM_MODEL=claude-sonnet-4-6
BROWSER_HEADLESS=true
CORS_ORIGINS=http://YOUR_DOMAIN,https://YOUR_DOMAIN
EOF
```

Generate a secure `SECRET_KEY`:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

## Step 5: Build the Frontend

```bash
cd /opt/browseruse-app/frontend
npm install
npm run build
# Output: /opt/browseruse-app/frontend/dist/
```

## Step 6: Configure Nginx

```bash
cat > /etc/nginx/sites-available/browseruse << 'CONF'
server {
    listen 80;
    server_name YOUR_DOMAIN_OR_IP;

    # React frontend (static files)
    root /opt/browseruse-app/frontend/dist;
    index index.html;

    # API → FastAPI
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
    }

    # Health check
    location /health {
        proxy_pass http://127.0.0.1:8000;
    }

    # SPA fallback
    location / {
        try_files $uri $uri/ /index.html;
    }

    client_max_body_size 20M;
}
CONF

ln -sf /etc/nginx/sites-available/browseruse /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx
```

## Step 7: Create systemd Service

```bash
cat > /etc/systemd/system/browseruse.service << 'EOF'
[Unit]
Description=BrowserUse FastAPI App
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/browseruse-app
Environment="PATH=/opt/browseruse-app/.venv/bin:/usr/local/bin:/usr/bin"
EnvironmentFile=/opt/browseruse-app/.env
ExecStart=/opt/browseruse-app/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable browseruse
systemctl start browseruse
```

## Step 8: Verify

```bash
# Check service status
systemctl status browseruse

# View live logs
journalctl -u browseruse -f

# Test health endpoint
curl http://localhost:8000/health

# Test from outside
curl http://YOUR_SERVER_IP/health
```

Visit `http://YOUR_SERVER_IP` in a browser — you should see the login page.

---

## SSL (HTTPS) with Let's Encrypt

```bash
apt install -y certbot python3-certbot-nginx
certbot --nginx -d yourdomain.com
# Auto-renews via systemd timer
```

---

## Updating the Application

```bash
cd /opt/browseruse-app
git pull origin main

# Rebuild frontend if changed
cd frontend && npm install && npm run build && cd ..

# Reinstall Python deps if changed
source .venv/bin/activate && uv sync

# Restart
systemctl restart browseruse
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `playwright` not found | Run `playwright install --with-deps chromium` inside the venv |
| Browser crashes on VPS | Ensure `BROWSER_HEADLESS=true` in `.env` |
| 502 Bad Gateway | Check if uvicorn is running: `systemctl status browseruse` |
| Port 8000 Refused | This is expected! Access the API via `http://YOUR_IP/api/health` instead |
| CORS errors | Add your domain to `CORS_ORIGINS` in `.env` and restart |
| Out of memory | Reduce `MAX_CONCURRENCY` to `1` or upgrade VPS RAM |
| Permission denied | Ensure `/opt/browseruse-app/uploads/` is writable |
