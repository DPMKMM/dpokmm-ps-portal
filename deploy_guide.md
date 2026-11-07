# Cloudflare Deployment Guide: https://dpokmm.panchayatautomation.in/ps-data

This portal hosts **Details of Panchayat Secretaries Working in Khammam District (PS Details – Khammam)**, available exclusively via **Cloudflare Zero Trust Edge Network** on your custom domain:

👉 **`https://dpokmm.panchayatautomation.in/ps-data`**

---

## 1. Cloud Architecture & Zero-Disturbance Guarantee

```
+---------------------------------------------------------------------------------+
|                       Cloudflare Edge Network & DNS                             |
|                         (panchayatautomation.in)                                |
+---------------------------------------+-----------------------------------------+
                                        |
       +--------------------------------+--------------------------------+
       |                                                                 |
[ Root Domain: @ ]                                            [ Subdomain: dpokmm ]
panchayatautomation.in                                        dpokmm.panchayatautomation.in
       |                                                                 |
       v                                                                 v
[ Cloudflare Zero Trust Tunnel ]                              [ Cloudflare Zero Trust Tunnel ]
Office Desktop (ePanchayat)                                   PS Details – Khammam (Port 8000)
100% UNTOUCHED & UNDISTURBED                                  EXCLUSIVELY SERVES /ps-data
```

- **Render Removed Completely:** No external third-party domains (`onrender.com`).
- **Exclusive URL:** The application is routed strictly and exclusively through `https://dpokmm.panchayatautomation.in/ps-data`.
- **Existing Website Untouched:** `https://www.panchayatautomation.in/` remains undisturbed.

---

## 2. One-Time Step: Add Public Hostname in Cloudflare Zero Trust Dashboard

1. Log in to **[Cloudflare Zero Trust Dashboard](https://one.dash.cloudflare.com/)**.
2. Navigate to **Networks** → **Tunnels**.
3. Click your existing tunnel (`e57ffde8-ddcc-4528-8655-68ffa09e0222`) and select **Configure**.
4. Switch to the **Public Hostnames** tab.
5. Click **Add a public hostname**:
   - **Subdomain:** `dpokmm`
   - **Domain:** `panchayatautomation.in`
   - **Path:** *(leave blank to forward all paths, or enter `ps-data`)*
   - **Service Type:** `HTTP`
   - **URL:** `localhost:8000` (or `127.0.0.1:8000`)
6. Click **Save hostname**.

*(Optional for `www.dpokmm`)*: Add another public hostname with Subdomain `www.dpokmm`, Domain `panchayatautomation.in`, URL `localhost:8000`.

---

## 3. How to Launch the Portal

To start the portal and connect to the Cloudflare Zero Trust Tunnel:

### Option 1 (One-Click):
Double-click **`Start_Portal.bat`** in this folder.

### Option 2 (Command Line):
```bash
python run_cloudflare_portal.py
```

The script will:
1. Verify the local portal server is active on `http://127.0.0.1:8000`.
2. Connect to the Cloudflare Zero Trust edge network via `cloudflared.exe`.
3. Keep the public address **`https://dpokmm.panchayatautomation.in/ps-data`** live and secure.

---

## 4. Preloaded Admin & Mandal Login Credentials

### District Super Admin (All 20 Mandals & 571 GPs)
- **Username:** `admin`
- **Password:** `Admin@Khammam2026`

### Mandal Admins (Single Active Session Enforced)
- **Username:** `<mandal_name>` (e.g. `kallur`, `enkoor`, `sathupally`, `penubally`, `thallada`)
- **Password:** `Mandal@<Mandal_LGD>` (e.g. `Mandal@5069` for Kallur, `Mandal@5065` for Enkoor)

### District Collectorate Read-Only Viewer
- **Username:** `viewer`
- **Password:** `Viewer@Khammam2026`
