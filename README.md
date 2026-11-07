# Details of Panchayat Secretaries Working in Khammam District
### Short Application Name: **PS Details – Khammam**
**Department:** District Panchayat Office, Khammam, Telangana  
**Coverage:** All 571 Gram Panchayats & 20 Mandals  
**System Type:** Panchayat Secretary Posting, Deputation, Salary Mapping and Employee Availability Management System

---

## 1. Executive Summary & Problem Solved

Khammam District comprises **571 Gram Panchayats** distributed across **20 Mandals**. While each Gram Panchayat has a sanctioned Panchayat Secretary post, actual posting dynamics involve complex deputation chains, including:
- Employees drawing salary from one GP but deputed to another GP within the same Mandal.
- Cross-Mandal deputations within Khammam District.
- Deputations to offices/districts outside Khammam while drawing salary from a Khammam GP.
- Complicated multi-hop chains (e.g. Employee A: GP-001 → GP-003, Employee B: GP-003 → GP-008, Employee C: GP-008 → GP-015, Employee D: GP-015 → GP-025).
- Employees on suspension, absconding, medical, maternity, or long leave.

**PS Details – Khammam** provides a single centralized database and web portal to establish:
1. Exactly where every employee draws salary.
2. Where every employee is physically working.
3. The real-time employee service status (Working, Suspended, Absconding, 8 Leave types).
4. Genuine on-ground employee availability per Gram Panchayat (excluding suspended/absconding/leave personnel without automatically creating a false clear vacancy).
5. Two-side deputation verification to ensure receiving Mandals confirm physical joining before deputations are considered verified.

---

## 2. Key Architecture & Security Specifications

### A. Centralized Master Data (571 GPs & 20 Mandals)
- **Zero Manual Typing:** Gram Panchayat names, LGD codes, and Mandal mappings are centrally locked. Mandal users select from preloaded dropdowns.
- **Strict LGD Identifier Enforcement:** Every Gram Panchayat is identified by its unique **Panchayat LGD Code** (e.g., `202319` for Arikayalapadu, Enkoor Mandal). Names are never used as primary database keys.
- **District Admin Control:** Complete master dataset preloaded directly from official government records (`LGD Codes.xlsx`).

### B. Single Active Login Session Restriction (Section 5)
- **Mandatory Enforcement:** Each Mandal account permits only **ONE active session** at any time.
- **Concurrency Protection:** If a Mandal account is logged in on Desktop A, any attempt to log in from Desktop B or mobile is rejected with:
  > *"This Mandal account is already logged in on another device. Please logout from the existing device before attempting a new login."*
- **15-Minute Inactivity Auto-Logout:** Active sessions automatically expire after 15 minutes of inactivity.
- **Brute Force Lockout:** Accounts are locked after 5 consecutive failed login attempts, unlockable by District Super Admin.
- **Password Security:** Hashes stored using modern **Argon2id** (`argon2-cffi`).
- **Super Admin Session Control:** District Super Admin can monitor active sessions across all 20 Mandals and force-terminate unauthorized sessions.

### C. Global Employee ID Duplicate Validation (Section 7)
- **Real-Time Instant Search:** While typing or changing fields, the backend queries the district-wide database across all 20 Mandals.
- **Duplicate Prevention:** If an Employee ID is already registered, the application displays:
  > **"EMPLOYEE ALREADY EXISTS!"**  
  > *"This Employee ID is already registered in Details of Panchayat Secretaries Working in Khammam District. Duplicate employee registration is not permitted."*
- **Safe Information Display:** Shows where their salary is claimed and where they are working, while **hiding sensitive personal information (DOB)** from unauthorized users.
- **Audit Logging:** Every duplicate registration attempt is logged in `duplicate_validation_logs`.

### D. Automatic Deputation Chain Tracking Engine (Section 8)
- **Graph & Chain Analyzer:** Traces interconnected deputation links across Mandals.
- **Circular Reference Detection:** Flags circular assignments (e.g., GP-A → GP-B → GP-A) and broken links.
- **Interactive Visualizer:** Renders directed graph diagrams on canvas showing nodes (GPs) and directed edges (employees).
- **Independent Tracking Logic:** Deputation of Employee A into GP-X does not automatically assume Employee B vacated GP-X; every employee's status is tracked independently.

### E. Two-Side Deputation Verification (Section 14)
- **Verification States:**
  1. `Pending Verification`
  2. `Verified by Salary-Claiming GP`
  3. `Verified by Receiving GP`
  4. `Verified by Both GPs`
  5. `Rejected`
  6. `Discrepancy`
- **Receiving Mandal Confirmation:** When Mandal A reports an employee deputed to Mandal B, Mandal B sees an incoming request in their *Verification Centre* to confirm or reject physical joining.

### F. Real-Time Discrepancy Detection Engine (Section 15)
Automated detection of 19 government compliance rules:
1. Clear vacancy marked despite active salary mapping.
2. Expected joining date passed without status update (*"STATUS UPDATE REQUIRED – VERIFY ACTUAL EMPLOYEE STATUS"*).
3. Expired deputation orders.
4. Two-side unverified deputations.
5. Suspended employees lacking suspension order numbers.
6. Absconding cases without disciplinary proceedings initiated.
7. Inter-district deputations missing destination office details.
8. Unresolved duplicate attempts.

### G. Statutory Reports (26 Reports A to Z - Section 17)
All reports available for on-screen viewing, **Excel (.xlsx)** export, **CSV** export, and official government print layout:
- **Report A:** District Employee Master Report
- **Report B:** Mandal-wise Panchayat Secretary Status Report
- **Report C:** GP-wise Employee Position Report
- **Report D:** Salary-Claiming GP vs Actual Working GP Report
- **Report E:** Deputation Within Same Mandal Report
- **Report F:** Deputation to Other Mandals Report
- **Report G:** Deputation to Other Districts Report
- **Report H:** Clear Vacancy Report
- **Report I:** Suspended Employees Report
- **Report J:** Absconding Employees Report
- **Report K:** Long Leave Employees Report
- **Report L:** Medical Leave Employees Report
- **Report M:** Maternity and Child Care Leave Report
- **Report N:** Other Approved Leave Report
- **Report O:** Employees Not Available for Regular Work Report
- **Report P:** Expected Joining Date Crossed Report
- **Report Q:** Employee-wise Deputation Chain Report
- **Report R:** Duplicate and Conflicting Employee Report
- **Report S:** Unverified Deputation Report
- **Report T:** GP-wise Employees Actually Working Report
- **Report U:** Salary-Claiming GP with No Employee Actually Working
- **Report V:** Employees Working Without Matching Salary-Claiming Records
- **Report W:** Mandal-wise Data Submission Status Report
- **Report X:** GP-wise Deputation In and Deputation Out Report
- **Report Y:** Employee Service Status History Report
- **Report Z:** Employee Availability vs Salary Claiming Strength Report

---

## 3. Preloaded Access Credentials

### A. District Super Admin
- **Username:** `admin`
- **Password:** `Admin@Khammam2026`
- **Privileges:** Complete district access, user management, force logout, audit logs, discrepancy resolution, lock/reopen Mandal submissions.

### B. Mandal Admin Accounts (20 Mandals)
Each Mandal user has access strictly isolated to their own Mandal:

| S.No | Mandal Name | Mandal LGD | Username | Default Password |
|---|---|---|---|---|
| 1 | Enkoor | 5065 | `enkoor` | `Mandal@5065` |
| 2 | Kallur | 5069 | `kallur` | `Mandal@5069` |
| 3 | Penubally | 5084 | `penubally` | `Mandal@5084` |
| 4 | Sathupally | 5086 | `sathupally` | `Mandal@5086` |
| 5 | Thallada | 5089 | `thallada` | `Mandal@5089` |
| 6 | Vemsoor | 5093 | `vemsoor` | `Mandal@5093` |
| 7 | Bonakal | 5057 | `bonakal` | `Mandal@5057` |
| 8 | Chinthakani | 5061 | `chinthakani` | `Mandal@5061` |
| 9 | Kamepally | 5070 | `kamepally` | `Mandal@5070` |
| 10 | Khammam (Rural) | 5071 | `khammamrural` | `Mandal@5071` |
| 11 | Konijerla | 5073 | `konijerla` | `Mandal@5073` |
| 12 | Kusumanchi | 5077 | `kusumanchi` | `Mandal@5077` |
| 13 | Madhira | 5078 | `madhira` | `Mandal@5078` |
| 14 | Mudigonda | 5080 | `mudigonda` | `Mandal@5080` |
| 15 | Nelakondapally | 5082 | `nelakondapally` | `Mandal@5082` |
| 16 | Raghunadhapalem | 7258 | `raghunadhapalem` | `Mandal@7258` |
| 17 | Singareni | 5087 | `singareni` | `Mandal@5087` |
| 18 | Thirumalayapalem | 5090 | `thirumalayapalem` | `Mandal@5090` |
| 19 | Wyra | 5096 | `wyra` | `Mandal@5096` |
| 20 | Yerrupalem | 5098 | `yerrupalem` | `Mandal@5098` |

### C. District Viewer (Collectorate Read-Only Access)
- **Username:** `viewer`
- **Password:** `Viewer@Khammam2026`

---

## 4. Running the Application

### Start Application Server:
```powershell
python run.py
```
Or directly using Uvicorn:
```powershell
uvicorn app.main:app --host 127.0.0.1 --port 8080
```

### Access Application:
Open your browser and navigate to:
```
http://127.0.0.1:8080
```

### Run Automated Test Suite:
```powershell
python test_app.py
```
