# Deployment Guide: Hosting at https://www.dpokmm.panchayatautomation.in/psdata

This guide provides step-by-step instructions for hosting **Details of Panchayat Secretaries Working in Khammam District** on your domain **`panchayatautomation.in`** under the dedicated subdomain and path:

👉 **`https://www.dpokmm.panchayatautomation.in/psdata`**

---

## 1. Domain & DNS Configuration

1. Log in to your domain registrar / DNS manager (Cloudflare, GoDaddy, Hostinger, Namecheap, etc.) for `panchayatautomation.in`.
2. Add the following DNS records:
   - **Type:** `A`  
     **Name / Host:** `dpokmm`  
     **Value / Target:** Your Server Public IP (e.g., `123.45.67.89`)  
     **TTL:** Automatic / 300 seconds
   - **Type:** `CNAME`  
     **Name / Host:** `www.dpokmm`  
     **Value / Target:** `dpokmm.panchayatautomation.in`

---

## 2. Server Deployment Options

### Option A: Standard VPS / Cloud Server (Ubuntu / Debian / Nginx)

#### Step 1: Upload Files
Upload the project folder contents to your production server directory, for example:
```bash
sudo mkdir -p /var/www/dpokmm_ps_database
# Copy/rsync all project files into /var/www/dpokmm_ps_database
```

#### Step 2: Install Python & Dependencies
```bash
sudo apt update && sudo apt install -y python3 python3-pip python3-venv nginx certbot python3-certbot-nginx
cd /var/www/dpokmm_ps_database
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt # Or install fastapi uvicorn argon2-cffi openpyxl reportlab pyjwt httpx
```

#### Step 3: Enable Systemd Service
Copy the provided unit file:
```bash
sudo cp khammam_ps.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable khammam_ps
sudo systemctl start khammam_ps
sudo systemctl status khammam_ps
```

#### Step 4: Configure Nginx & SSL Certificate
```bash
sudo cp nginx.conf /etc/nginx/sites-available/dpokmm.panchayatautomation.in
sudo ln -s /etc/nginx/sites-available/dpokmm.panchayatautomation.in /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Issue free SSL Certificate with Let's Encrypt
sudo certbot --nginx -d dpokmm.panchayatautomation.in -d www.dpokmm.panchayatautomation.in
```

---

### Option B: cPanel / Shared Hosting (via Setup Python App)

If your website `panchayatautomation.in` is hosted on cPanel:

1. **Create Subdomain in cPanel:**
   - Go to **Domains** → **Create A New Domain**.
   - Domain: `dpokmm.panchayatautomation.in`
   - Document Root: `public_html/dpokmm`
2. **Setup Python Application:**
   - In cPanel, search for **Setup Python App**.
   - Click **Create Application**.
   - Python Version: `3.10` or `3.11` or `3.12`.
   - Application Root: `dpokmm_ps_database`
   - Application URL: `dpokmm.panchayatautomation.in/psdata` (or root).
   - Application Startup File: `passenger_wsgi.py` (or run Uvicorn reverse proxy).
3. **Using Apache Reverse Proxy (`.htaccess`):**
   If running Uvicorn on port `8000` via background daemon, add this to `public_html/dpokmm/.htaccess`:
   ```apache
   RewriteEngine On
   RewriteRule ^psdata/(.*)$ http://127.0.0.1:8000/psdata/$1 [P,L]
   RewriteRule ^psdata$ http://127.0.0.1:8000/psdata [P,L]
   ```

---

## 3. Link from Main Website (https://www.panchayatautomation.in/)

To link this portal from your main website homepage or menu, simply add this anchor button:

```html
<a href="https://www.dpokmm.panchayatautomation.in/psdata" target="_blank" class="btn-portal">
  <span>District Panchayat Office, Khammam</span>
  <strong>Panchayat Secretaries Database & Deputation Portal</strong>
</a>
```

---

## 4. Dual-Path Routing Verified

The application is engineered to work seamlessly on both routes:
- `https://www.dpokmm.panchayatautomation.in/psdata`
- `http://127.0.0.1:8000/` (Local / development)

All asset links (`/static/...`), API endpoints (`/api/...`), and exports automatically adapt their paths based on the current URL prefix.
