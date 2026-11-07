# Cloud Deployment & DNS Setup Guide: https://www.dpokmm.panchayatautomation.in/ps-data

This portal hosts **Details of Panchayat Secretaries Working in Khammam District (PS Details – Khammam)** completely in the cloud, independent of your office desktop.

---

## 1. Cloud Architecture & Zero-Disturbance Guarantee

```
+-------------------------------------------------------------+
|                 Cloudflare DNS Manager                       |
|               (panchayatautomation.in)                      |
+------------------------------+------------------------------+
                               |
       +-----------------------+-----------------------+
       |                                               |
[ Root Domain: @ ]                         [ Subdomain: dpokmm ]
panchayatautomation.in                     dpokmm.panchayatautomation.in
       |                                               |
       v                                               v
[ Cloudflare Zero Trust Tunnel ]           [ Cloud Host (Render) ]
Office Desktop (ePanchayat)                dpokmm-ps-portal.onrender.com
100% UNTOUCHED & UNDISTURBED               100% INDEPENDENT CLOUD
```

- **Office Desktop Remains 100% Untouched:** Your existing site (`https://panchayatautomation.in/`) running via Cloudflare Tunnel from your office desktop continues running exactly as before without any changes.
- **Dedicated Cloud Service:** The new portal is deployed on **Render** (Singapore Region) backed by GitHub repository [`DPMKMM/dpokmm-ps-portal`](https://github.com/DPMKMM/dpokmm-ps-portal).
- **24/7 Uptime:** Even if the office desktop is turned off, restarted, or disconnected, the cloud portal remains live.

---

## 2. Live Cloud Service Details

- **GitHub Repository:** [https://github.com/DPMKMM/dpokmm-ps-portal](https://github.com/DPMKMM/dpokmm-ps-portal)
- **Direct Cloud URL:** [https://dpokmm-ps-portal.onrender.com/ps-data](https://dpokmm-ps-portal.onrender.com/ps-data)
- **Health Check Endpoint:** [https://dpokmm-ps-portal.onrender.com/health](https://dpokmm-ps-portal.onrender.com/health)
- **Render Dashboard:** [https://dashboard.render.com/web/srv-dbna1d5g1s2s73c3vveg](https://dashboard.render.com/web/srv-dbna1d5g1s2s73c3vveg)
- **Service ID:** `srv-dbna1d5g1s2s73c3vveg`
- **Region:** Singapore

---

## 3. One-Time Step: Cloudflare DNS Configuration

To activate your custom domain `https://dpokmm.panchayatautomation.in/ps-data` and `https://www.dpokmm.panchayatautomation.in/ps-data`:

1. Log in to your **Cloudflare Dashboard** at [https://dash.cloudflare.com/](https://dash.cloudflare.com/).
2. Select your domain **`panchayatautomation.in`**.
3. In the left sidebar, click **DNS** -> **Records**.
4. Click **Add record** and enter:
   - **Type:** `CNAME`
   - **Name:** `dpokmm`
   - **Target:** `dpokmm-ps-portal.onrender.com`
   - **Proxy status:** `Proxied` (Orange Cloud) or `DNS only` (Grey Cloud)
   - **TTL:** Auto
5. Click **Save**.
6. *(Optional for `www.dpokmm`)* Click **Add record** again:
   - **Type:** `CNAME`
   - **Name:** `www.dpokmm`
   - **Target:** `dpokmm-ps-portal.onrender.com`
   - **Proxy status:** `Proxied` (Orange Cloud)
   - **TTL:** Auto
7. Click **Save**.

> **Note:** Because this only creates the `dpokmm` and `www.dpokmm` subdomains, your root domain (`panchayatautomation.in`) and its Cloudflare Tunnel to your office desktop are completely unaffected.

---

## 4. Automatic Continuous Deployment (CI/CD)

Whenever you push any updates or fixes to `main`:
```bash
git add .
git commit -m "Update portal features"
git push origin main
```
Render will automatically detect the commit, rebuild the Docker container, and deploy the new version with zero manual intervention.

---

## 5. Preloaded Admin & Mandal Login Credentials

### District Super Admin (All 20 Mandals & 571 GPs)
- **Username:** `admin`
- **Password:** `Admin@Khammam2026`

### Mandal Admins (Single Active Session Enforced)
- **Username:** `<mandal_name>` (e.g. `kallur`, `enkoor`, `sathupally`, `penubally`, `thallada`)
- **Password:** `Mandal@<Mandal_LGD>` (e.g. `Mandal@5069` for Kallur, `Mandal@5065` for Enkoor)

### District Collectorate Read-Only Viewer
- **Username:** `viewer`
- **Password:** `Viewer@Khammam2026`
