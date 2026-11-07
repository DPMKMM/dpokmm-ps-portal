"""
Seed script to populate test data with the exact CSV provided by the user:
- Total GPs: 571 across 20 Mandals
- 5% GPs Clear Vacant (~29 GPs)
- 511 Unique Employees from user CSV:
  - Working: 45% (~230 emps)
  - Deputation: 35% (~179 emps)
  - Leave: 10% (~51 emps)
  - Absconding: 1% (~5 emps)
  - Suspended: 9% (~46 emps)
"""

import csv
import random
from datetime import date, datetime, timedelta
from app.database import SessionLocal
from app.models import (
    Employee, EmployeeSalaryMapping, EmployeePosting, EmployeeStatusHistory,
    GramPanchayat, Mandal, InternalReassignment, GPVerification, DiscrepancyRecord
)

random.seed(42)  # For reproducible test data

def run_seed():
    db = SessionLocal()
    print("=" * 70)
    print("STARTING TEST DATA POPULATION FROM USER CSV")
    print("=" * 70)

    # 1. Clean existing employee and transaction tables
    print("1. Cleaning old records...")
    db.query(DiscrepancyRecord).delete()
    db.query(GPVerification).delete()
    db.query(InternalReassignment).delete()
    db.query(EmployeeStatusHistory).delete()
    db.query(EmployeePosting).delete()
    db.query(EmployeeSalaryMapping).delete()
    db.query(Employee).delete()
    db.commit()

    # 2. Load Mandals & GPs from DB
    mandals = db.query(Mandal).all()
    mandal_by_id = {m.id: m for m in mandals}
    mandal_by_name = {m.mandal_name.lower(): m for m in mandals}
    all_gps = db.query(GramPanchayat).all()
    gp_by_lgd = {g.lgd_code: g for g in all_gps}
    gps_by_mandal = {}
    for g in all_gps:
        gps_by_mandal.setdefault(g.mandal_id, []).append(g)

    print(f"Loaded {len(mandals)} Mandals and {len(all_gps)} GPs from database.")

    # 3. Read user CSV
    with open('raw_user_employees.csv', mode='r', encoding='utf-8') as f:
        csv_rows = list(csv.DictReader(f))

    print(f"Read {len(csv_rows)} rows from user CSV.")

    # 4. Designate 29 GPs (5.08% of 571) as Clear Vacancies (1 or 2 per mandal)
    clear_vacant_gps = []
    for m in mandals:
        m_gps = gps_by_mandal.get(m.id, [])
        # Pick 1 or 2 per mandal to reach exactly 29
        count_to_pick = 2 if len(clear_vacant_gps) + (len(mandals) - mandals.index(m)) * 1 < 29 else 1
        picked = random.sample(m_gps, min(count_to_pick, len(m_gps)))
        clear_vacant_gps.extend(picked)
        if len(clear_vacant_gps) >= 29:
            break
    clear_vacant_gps = clear_vacant_gps[:29]
    clear_vacant_lgds = set(g.lgd_code for g in clear_vacant_gps)

    print(f"Selected {len(clear_vacant_gps)} Clear Vacant GPs (~5% of 571).")
    for g in all_gps:
        if g.lgd_code in clear_vacant_lgds:
            g.is_clear_vacancy = True
            g.vacancy_reason = "Clear Vacancy (No Regular PS Attached)"
        else:
            g.is_clear_vacancy = False
            g.vacancy_reason = None
    db.commit()

    # 5. Extract unique employees from CSV
    # Each employee has a primary salary GP from their first occurrence (preferably non-clear-vacant)
    emp_map = {}
    for r in csv_rows:
        emp_id = r['Panchayat Secretary Employee Id'].strip().upper()
        lgd = int(r['Panchayat LGD Code'].strip())
        name = r['Panchayat Secretary Name'].strip()
        desig = r['Designation'].strip()
        mobile = r['Mobile Number'].strip()
        m_name = r['Mandal Name'].strip()

        # Map designation to standard forms
        if "Outsourcing" in desig or "Contract" in desig or "CPS" in desig or desig == "OPS":
            desig = "OPS (Out Sourcing Panchayat Secretary)"
        elif "Grade I" in desig and "Grade IV" not in desig:
            desig = "Panchayat Secretary Grade-I"
        elif "Grade II" in desig:
            desig = "Panchayat Secretary Grade-II"
        elif "Grade III" in desig:
            desig = "Panchayat Secretary Grade-III"
        elif "Grade IV" in desig:
            desig = "Panchayat Secretary Grade-IV"
        elif "Junior" in desig:
            desig = "Junior Panchayat Secretary (JPS)"

        if emp_id not in emp_map:
            emp_map[emp_id] = {
                'employee_id': emp_id,
                'name': name,
                'designation': desig,
                'mobile': mobile if len(mobile) == 10 and mobile.isdigit() else f"9{random.randint(100000000, 999999999)}",
                'salary_gp_lgd': lgd,
                'mandal_name': m_name
            }
        else:
            # If current chosen GP is in clear vacant, swap to this one if not clear vacant
            if emp_map[emp_id]['salary_gp_lgd'] in clear_vacant_lgds and lgd not in clear_vacant_lgds:
                emp_map[emp_id]['salary_gp_lgd'] = lgd

    unique_employees = list(emp_map.values())
    total_emps = len(unique_employees)
    print(f"Total unique employees to seed: {total_emps}")

    # If any employee's chosen GP is in clear vacant list, find an available non-vacant GP
    available_non_vacant = [g for g in all_gps if g.lgd_code not in clear_vacant_lgds]
    for e in unique_employees:
        if e['salary_gp_lgd'] in clear_vacant_lgds:
            # Reassign salary GP to a non-vacant GP from the same mandal if possible
            m = mandal_by_name.get(e['mandal_name'].lower())
            if m:
                m_non_vacant = [g for g in gps_by_mandal[m.id] if g.lgd_code not in clear_vacant_lgds]
                if m_non_vacant:
                    e['salary_gp_lgd'] = random.choice(m_non_vacant).lgd_code
                else:
                    e['salary_gp_lgd'] = random.choice(available_non_vacant).lgd_code
            else:
                e['salary_gp_lgd'] = random.choice(available_non_vacant).lgd_code

    # 6. Partition employees by target percentages:
    # Working: 45% (~230)
    # Deputation: 35% (~179)
    # Leave: 10% (~51)
    # Absconding: 1% (~5)
    # Suspended: Remaining 9% (~46)
    n_working = int(round(total_emps * 0.45))      # 230
    n_deputation = int(round(total_emps * 0.35))   # 179
    n_leave = int(round(total_emps * 0.10))        # 51
    n_absconding = int(round(total_emps * 0.01))   # 5
    n_suspended = total_emps - (n_working + n_deputation + n_leave + n_absconding)  # 46

    print(f"Partition counts: Working={n_working} ({n_working/total_emps*100:.1f}%), "
          f"Deputation={n_deputation} ({n_deputation/total_emps*100:.1f}%), "
          f"Leave={n_leave} ({n_leave/total_emps*100:.1f}%), "
          f"Absconding={n_absconding} ({n_absconding/total_emps*100:.1f}%), "
          f"Suspended={n_suspended} ({n_suspended/total_emps*100:.1f}%)")

    random.shuffle(unique_employees)
    working_emps = unique_employees[:n_working]
    idx1 = n_working
    deputation_emps = unique_employees[idx1:idx1 + n_deputation]
    idx2 = idx1 + n_deputation
    leave_emps = unique_employees[idx2:idx2 + n_leave]
    idx3 = idx2 + n_leave
    absconding_emps = unique_employees[idx3:idx3 + n_absconding]
    idx4 = idx3 + n_absconding
    suspended_emps = unique_employees[idx4:]

    # 7. Insert all Employees into DB
    now = datetime.utcnow()
    for e in unique_employees:
        gp = gp_by_lgd[e['salary_gp_lgd']]
        birth_year = random.randint(1975, 1998)
        birth_month = random.randint(1, 12)
        birth_day = random.randint(1, 28)
        dob_val = date(birth_year, birth_month, birth_day)

        db_emp = Employee(
            employee_id=e['employee_id'],
            name_ifmis=e['name'],
            dob=dob_val,
            mobile_number=e['mobile'],
            designation=e['designation'],
            registration_mandal_id=gp.mandal_id,
            is_active=True,
            created_by="admin",
            created_at=now - timedelta(days=random.randint(60, 365))
        )
        db.add(db_emp)
    db.commit()
    print("Successfully created Employee Master records.")

    # 8. Create Working Employees (45%)
    # - Drawing salary from own GP, working in own GP
    for e in working_emps:
        gp = gp_by_lgd[e['salary_gp_lgd']]
        joining_date = date(random.randint(2019, 2024), random.randint(1, 12), random.randint(1, 28))

        sm = EmployeeSalaryMapping(
            employee_id=e['employee_id'],
            salary_gp_lgd=gp.lgd_code,
            salary_mandal_id=gp.mandal_id,
            salary_claiming_status="YES",
            service_status="WORKING",
            effective_from=joining_date,
            is_active=True,
            created_by="admin",
            created_at=now
        )
        db.add(sm)

        post = EmployeePosting(
            employee_id=e['employee_id'],
            is_working_in_salary_gp=True,
            posting_type="OWN_GP",
            actual_working_gp_lgd=gp.lgd_code,
            actual_working_mandal_id=gp.mandal_id,
            official_deputation_gp_lgd=gp.lgd_code,
            official_deputation_mandal_id=gp.mandal_id,
            effective_from=joining_date,
            verification_status="VERIFIED",
            is_current=True,
            remarks="Regular active duty at salary-claiming Gram Panchayat."
        )
        db.add(post)

        sh = EmployeeStatusHistory(
            employee_id=e['employee_id'],
            service_status="WORKING",
            status_effective_from=joining_date,
            is_current=True,
            reason_remarks="Regular duty",
            updated_by="admin",
            updated_at=now
        )
        db.add(sh)

    db.commit()
    print("Created Working (45%) mappings.")

    # 9. Create Deputation Employees (35%)
    # Subdivided into:
    # - Within Same Mandal (~80)
    # - To Another Mandal in Khammam (~75) [25 with Internal Reassignment]
    # - To Other District (~16)
    # - To Other Department (~8)
    n_dep_same_mandal = 80
    n_dep_other_mandal = 75
    n_dep_other_dist = 16
    n_dep_other_dept = len(deputation_emps) - (n_dep_same_mandal + n_dep_other_mandal + n_dep_other_dist)

    dep_same_mandal_list = deputation_emps[:n_dep_same_mandal]
    d_idx1 = n_dep_same_mandal
    dep_other_mandal_list = deputation_emps[d_idx1:d_idx1 + n_dep_other_mandal]
    d_idx2 = d_idx1 + n_dep_other_mandal
    dep_other_dist_list = deputation_emps[d_idx2:d_idx2 + n_dep_other_dist]
    d_idx3 = d_idx2 + n_dep_other_dist
    dep_other_dept_list = deputation_emps[d_idx3:]

    # A. Within Same Mandal
    for e in dep_same_mandal_list:
        sal_gp = gp_by_lgd[e['salary_gp_lgd']]
        # Pick another GP in the same mandal
        m_gps = [g for g in gps_by_mandal[sal_gp.mandal_id] if g.lgd_code != sal_gp.lgd_code]
        dest_gp = random.choice(m_gps) if m_gps else sal_gp
        joining_date = date(random.randint(2020, 2023), random.randint(1, 12), random.randint(1, 28))
        dep_date = date(2025, random.randint(1, 8), random.randint(1, 28))
        order_no = f"DLPO/DEP/MND/{random.randint(100, 999)}/2025"

        sm = EmployeeSalaryMapping(
            employee_id=e['employee_id'],
            salary_gp_lgd=sal_gp.lgd_code,
            salary_mandal_id=sal_gp.mandal_id,
            salary_claiming_status="YES",
            service_status="WORKING",
            effective_from=joining_date,
            is_active=True,
            created_by="admin",
            created_at=now
        )
        db.add(sm)

        post = EmployeePosting(
            employee_id=e['employee_id'],
            is_working_in_salary_gp=False,
            posting_type="WITHIN_MANDAL",
            actual_working_gp_lgd=dest_gp.lgd_code,
            actual_working_mandal_id=sal_gp.mandal_id,
            official_deputation_gp_lgd=dest_gp.lgd_code,
            official_deputation_mandal_id=sal_gp.mandal_id,
            deputation_order_no=order_no,
            deputation_order_date=dep_date,
            deputation_effective_from=dep_date,
            effective_from=dep_date,
            verification_status="VERIFIED",
            is_current=True,
            remarks=f"Deputed within same mandal from {sal_gp.gp_name} to {dest_gp.gp_name}."
        )
        db.add(post)

        sh = EmployeeStatusHistory(
            employee_id=e['employee_id'],
            service_status="WORKING",
            status_effective_from=dep_date,
            proceedings_order_no=order_no,
            is_current=True,
            reason_remarks="Deputed within same mandal",
            updated_by="admin",
            updated_at=now
        )
        db.add(sh)

    # B. To Another Mandal in Khammam (75 emps, 25 with Internal Reassignment)
    other_mandal_with_ir = dep_other_mandal_list[:25]
    other_mandal_regular = dep_other_mandal_list[25:]

    # B1. Regular Cross-Mandal Deputation (50 emps)
    for e in other_mandal_regular:
        sal_gp = gp_by_lgd[e['salary_gp_lgd']]
        dest_mandal_id = random.choice([m.id for m in mandals if m.id != sal_gp.mandal_id])
        dest_gps = gps_by_mandal[dest_mandal_id]
        dest_gp = random.choice(dest_gps)

        joining_date = date(random.randint(2019, 2023), random.randint(1, 12), random.randint(1, 28))
        dep_date = date(2025, random.randint(1, 10), random.randint(1, 28))
        order_no = f"DPO/KMM/DEP/{random.randint(100, 999)}/2025"

        sm = EmployeeSalaryMapping(
            employee_id=e['employee_id'],
            salary_gp_lgd=sal_gp.lgd_code,
            salary_mandal_id=sal_gp.mandal_id,
            salary_claiming_status="YES",
            service_status="WORKING",
            effective_from=joining_date,
            is_active=True,
            created_by="admin",
            created_at=now
        )
        db.add(sm)

        post = EmployeePosting(
            employee_id=e['employee_id'],
            is_working_in_salary_gp=False,
            posting_type="ANOTHER_MANDAL",
            actual_working_gp_lgd=dest_gp.lgd_code,
            actual_working_mandal_id=dest_mandal_id,
            official_deputation_gp_lgd=dest_gp.lgd_code,
            official_deputation_mandal_id=dest_mandal_id,
            deputation_order_no=order_no,
            deputation_order_date=dep_date,
            deputation_effective_from=dep_date,
            effective_from=dep_date,
            verification_status="VERIFIED",
            is_current=True,
            remarks=f"District Deputation Order: From {sal_gp.gp_name} ({sal_gp.mandal_name}) to {dest_gp.gp_name} ({dest_gp.mandal_name})."
        )
        db.add(post)

        sh = EmployeeStatusHistory(
            employee_id=e['employee_id'],
            service_status="WORKING",
            status_effective_from=dep_date,
            proceedings_order_no=order_no,
            is_current=True,
            reason_remarks=f"Deputed to {dest_gp.gp_name}",
            updated_by="admin",
            updated_at=now
        )
        db.add(sh)

    # B2. Cross-Mandal with Internal Reassignment (25 emps: Official GP-X -> Reassigned GP-Z)
    for e in other_mandal_with_ir:
        sal_gp = gp_by_lgd[e['salary_gp_lgd']]
        dest_mandal_id = random.choice([m.id for m in mandals if m.id != sal_gp.mandal_id])
        dest_gps = gps_by_mandal[dest_mandal_id]
        if len(dest_gps) >= 2:
            off_gp, pres_gp = random.sample(dest_gps, 2)
        else:
            off_gp = dest_gps[0]
            pres_gp = dest_gps[0]

        joining_date = date(random.randint(2019, 2023), random.randint(1, 12), random.randint(1, 28))
        dep_date = date(2025, random.randint(1, 6), random.randint(1, 28))
        ir_date = dep_date + timedelta(days=random.randint(15, 60))
        dpo_order_no = f"DPO/KMM/DEP/{random.randint(100, 999)}/2025"
        mpdo_order_no = f"MPDO/{mandal_by_id[dest_mandal_id].mandal_name[:3].upper()}/LOCAL/{random.randint(10, 99)}/2025"

        sm = EmployeeSalaryMapping(
            employee_id=e['employee_id'],
            salary_gp_lgd=sal_gp.lgd_code,
            salary_mandal_id=sal_gp.mandal_id,
            salary_claiming_status="YES",
            service_status="WORKING",
            effective_from=joining_date,
            is_active=True,
            created_by="admin",
            created_at=now
        )
        db.add(sm)

        post = EmployeePosting(
            employee_id=e['employee_id'],
            is_working_in_salary_gp=False,
            posting_type="ANOTHER_MANDAL",
            official_deputation_gp_lgd=off_gp.lgd_code,
            official_deputation_mandal_id=dest_mandal_id,
            actual_working_gp_lgd=pres_gp.lgd_code,
            actual_working_mandal_id=dest_mandal_id,
            has_internal_reassignment=True,
            reassigned_working_gp_lgd=pres_gp.lgd_code,
            deputation_order_no=dpo_order_no,
            deputation_order_date=dep_date,
            deputation_effective_from=dep_date,
            effective_from=ir_date,
            verification_status="VERIFIED",
            is_current=True,
            remarks=f"Officially deputed to {off_gp.gp_name} (X); internally reassigned by MPDO to {pres_gp.gp_name} (Z)."
        )
        db.add(post)
        db.flush()

        ir = InternalReassignment(
            posting_id=post.id,
            employee_id=e['employee_id'],
            original_deputation_gp_lgd=off_gp.lgd_code,
            reassigned_from_gp_lgd=off_gp.lgd_code,
            reassigned_to_gp_lgd=pres_gp.lgd_code,
            reassignment_date=ir_date,
            is_written_proceedings_available=True,
            proceedings_order_no=mpdo_order_no,
            reason_remarks="MPDO local administrative arrangement due to heavy Gram Panchayat workload and cluster coverage.",
            is_current=True,
            verified_by_user="admin",
            verified_at=now,
            created_at=now
        )
        db.add(ir)

        sh = EmployeeStatusHistory(
            employee_id=e['employee_id'],
            service_status="WORKING",
            status_effective_from=ir_date,
            proceedings_order_no=mpdo_order_no,
            is_current=True,
            reason_remarks=f"Internally reassigned to {pres_gp.gp_name}",
            updated_by="admin",
            updated_at=now
        )
        db.add(sh)

    # C. Other District Deputations (16 emps)
    ext_districts = ["Bhadradri Kothagudem", "Suryapet", "Mahabubabad", "Warangal", "Nalgonda"]
    ext_offices = ["O/o District Collector", "MPDO Office", "Zilla Praja Parishad", "Special Officer Duty", "Elections Division"]
    for e in dep_other_dist_list:
        sal_gp = gp_by_lgd[e['salary_gp_lgd']]
        joining_date = date(random.randint(2019, 2023), random.randint(1, 12), random.randint(1, 28))
        dep_date = date(2025, random.randint(1, 9), random.randint(1, 28))
        dist_name = random.choice(ext_districts)
        office_name = f"{random.choice(ext_offices)}, {dist_name}"
        order_no = f"GO/RT/PRRD/{random.randint(100, 999)}/2025"

        sm = EmployeeSalaryMapping(
            employee_id=e['employee_id'],
            salary_gp_lgd=sal_gp.lgd_code,
            salary_mandal_id=sal_gp.mandal_id,
            salary_claiming_status="YES",
            service_status="WORKING",
            effective_from=joining_date,
            is_active=True,
            created_by="admin",
            created_at=now
        )
        db.add(sm)

        post = EmployeePosting(
            employee_id=e['employee_id'],
            is_working_in_salary_gp=False,
            posting_type="OTHER_DISTRICT",
            external_district_name=dist_name,
            external_mandal_name="External",
            external_gp_or_office_name=office_name,
            deputation_order_no=order_no,
            deputation_order_date=dep_date,
            deputation_effective_from=dep_date,
            effective_from=dep_date,
            verification_status="VERIFIED",
            is_current=True,
            remarks=f"Deputed outside Khammam to {dist_name} ({office_name}). Drawing salary from {sal_gp.gp_name}."
        )
        db.add(post)

        sh = EmployeeStatusHistory(
            employee_id=e['employee_id'],
            service_status="WORKING",
            status_effective_from=dep_date,
            proceedings_order_no=order_no,
            is_current=True,
            reason_remarks=f"Deputed to {dist_name}",
            updated_by="admin",
            updated_at=now
        )
        db.add(sh)

    # D. Other Department Deputations (8 emps)
    ext_departments = ["Revenue (Tahsildar Office)", "DRDO / SERP", "Zilla Praja Parishad", "Tribal Welfare", "Health & Family Welfare"]
    for e in dep_other_dept_list:
        sal_gp = gp_by_lgd[e['salary_gp_lgd']]
        joining_date = date(random.randint(2019, 2023), random.randint(1, 12), random.randint(1, 28))
        dep_date = date(2025, random.randint(1, 9), random.randint(1, 28))
        dept_name = random.choice(ext_departments)
        office_name = f"District Branch ({dept_name}), Collectorate Complex, Khammam"
        order_no = f"PROC/DPO/DEPT/{random.randint(100, 999)}/2025"

        sm = EmployeeSalaryMapping(
            employee_id=e['employee_id'],
            salary_gp_lgd=sal_gp.lgd_code,
            salary_mandal_id=sal_gp.mandal_id,
            salary_claiming_status="YES",
            service_status="WORKING",
            effective_from=joining_date,
            is_active=True,
            created_by="admin",
            created_at=now
        )
        db.add(sm)

        post = EmployeePosting(
            employee_id=e['employee_id'],
            is_working_in_salary_gp=False,
            posting_type="OTHER_DEPARTMENT",
            external_department_name=dept_name,
            external_gp_or_office_name=office_name,
            deputation_order_no=order_no,
            deputation_order_date=dep_date,
            deputation_effective_from=dep_date,
            effective_from=dep_date,
            verification_status="VERIFIED",
            is_current=True,
            remarks=f"Deputed to {dept_name}. Salary drawn from {sal_gp.gp_name}."
        )
        db.add(post)

        sh = EmployeeStatusHistory(
            employee_id=e['employee_id'],
            service_status="WORKING",
            status_effective_from=dep_date,
            proceedings_order_no=order_no,
            is_current=True,
            reason_remarks=f"Deputed to {dept_name}",
            updated_by="admin",
            updated_at=now
        )
        db.add(sh)

    db.commit()
    print("Created Deputation (35%) mappings.")

    # 10. Create Leave Employees (10% - 51 emps)
    leave_types = (
        ["MEDICAL_LEAVE"] * 16 +
        ["MATERNITY_LEAVE"] * 12 +
        ["CHILD_CARE_LEAVE"] * 8 +
        ["EARNED_LEAVE"] * 8 +
        ["LONG_LEAVE"] * 7
    )
    for e, l_status in zip(leave_emps, leave_types):
        gp = gp_by_lgd[e['salary_gp_lgd']]
        joining_date = date(random.randint(2019, 2023), random.randint(1, 12), random.randint(1, 28))
        leave_from = date(2025, random.randint(10, 12), random.randint(1, 28)) if random.random() > 0.4 else date(2026, 1, random.randint(1, 28))
        proc_no = f"ROC/LEAVE/{l_status[:3]}/{random.randint(100, 999)}/2025"

        sm = EmployeeSalaryMapping(
            employee_id=e['employee_id'],
            salary_gp_lgd=gp.lgd_code,
            salary_mandal_id=gp.mandal_id,
            salary_claiming_status="YES",
            service_status=l_status,
            effective_from=joining_date,
            is_active=True,
            created_by="admin",
            created_at=now
        )
        db.add(sm)

        post = EmployeePosting(
            employee_id=e['employee_id'],
            is_working_in_salary_gp=True,
            posting_type="OWN_GP",
            actual_working_gp_lgd=gp.lgd_code,
            actual_working_mandal_id=gp.mandal_id,
            effective_from=joining_date,
            verification_status="PENDING",
            is_current=True,
            remarks=f"Currently on {l_status.replace('_', ' ').title()} from {leave_from}."
        )
        db.add(post)

        sh = EmployeeStatusHistory(
            employee_id=e['employee_id'],
            service_status=l_status,
            status_effective_from=leave_from,
            proceedings_order_no=proc_no,
            is_current=True,
            reason_remarks=f"Sanctioned {l_status.replace('_', ' ').title()}",
            updated_by="admin",
            updated_at=now
        )
        db.add(sh)

    db.commit()
    print("Created Leave (10%) records.")

    # 11. Create Absconding Employees (1% - 5 emps)
    for e in absconding_emps:
        gp = gp_by_lgd[e['salary_gp_lgd']]
        joining_date = date(random.randint(2019, 2022), random.randint(1, 12), random.randint(1, 28))
        abs_date = date(2025, random.randint(4, 9), random.randint(1, 28))
        memo_no = f"MEMO/DPO/ABS/{random.randint(10, 99)}/2025 (Show Cause Issued)"

        sm = EmployeeSalaryMapping(
            employee_id=e['employee_id'],
            salary_gp_lgd=gp.lgd_code,
            salary_mandal_id=gp.mandal_id,
            salary_claiming_status="YES",
            service_status="ABSCONDING",
            effective_from=joining_date,
            is_active=True,
            created_by="admin",
            created_at=now
        )
        db.add(sm)

        post = EmployeePosting(
            employee_id=e['employee_id'],
            is_working_in_salary_gp=True,
            posting_type="OWN_GP",
            actual_working_gp_lgd=gp.lgd_code,
            actual_working_mandal_id=gp.mandal_id,
            effective_from=joining_date,
            verification_status="FLAGGED",
            is_current=True,
            remarks=f"Absconding without authorization since {abs_date}. Disciplinary proceedings initiated."
        )
        db.add(post)

        sh = EmployeeStatusHistory(
            employee_id=e['employee_id'],
            service_status="ABSCONDING",
            status_effective_from=abs_date,
            proceedings_order_no=memo_no,
            is_current=True,
            reason_remarks="Unauthorized continuous absence from duty",
            updated_by="admin",
            updated_at=now
        )
        db.add(sh)

    db.commit()
    print("Created Absconding (1%) records.")

    # 12. Create Suspended Employees (9% - 46 emps)
    for e in suspended_emps:
        gp = gp_by_lgd[e['salary_gp_lgd']]
        joining_date = date(random.randint(2019, 2022), random.randint(1, 12), random.randint(1, 28))
        susp_date = date(2025, random.randint(6, 11), random.randint(1, 28))
        order_no = f"PROC/SUSP/DPO/KMM/{random.randint(10, 99)}/2025"

        sm = EmployeeSalaryMapping(
            employee_id=e['employee_id'],
            salary_gp_lgd=gp.lgd_code,
            salary_mandal_id=gp.mandal_id,
            salary_claiming_status="YES",
            service_status="SUSPENDED",
            effective_from=joining_date,
            is_active=True,
            created_by="admin",
            created_at=now
        )
        db.add(sm)

        post = EmployeePosting(
            employee_id=e['employee_id'],
            is_working_in_salary_gp=True,
            posting_type="OWN_GP",
            actual_working_gp_lgd=gp.lgd_code,
            actual_working_mandal_id=gp.mandal_id,
            effective_from=joining_date,
            verification_status="FLAGGED",
            is_current=True,
            remarks=f"Placed under suspension with effect from {susp_date} pending departmental inquiry."
        )
        db.add(post)

        sh = EmployeeStatusHistory(
            employee_id=e['employee_id'],
            service_status="SUSPENDED",
            status_effective_from=susp_date,
            proceedings_order_no=order_no,
            suspension_order_no=order_no,
            suspension_order_date=susp_date,
            suspension_effective_date=susp_date,
            is_current=True,
            reason_remarks="Placed under suspension vide Collector / DPO proceedings",
            updated_by="admin",
            updated_at=now
        )
        db.add(sh)

    db.commit()
    print("Created Suspended (9%) records.")

    # 13. Map 6 deputed employees to work in clear vacant GPs (demonstrating Deputation In to Vacant GP)
    vacant_sample = clear_vacant_gps[:6]
    deputed_to_reassign = deputation_emps[:6]
    for dep_e, vac_gp in zip(deputed_to_reassign, vacant_sample):
        post = db.query(EmployeePosting).filter(EmployeePosting.employee_id == dep_e['employee_id']).first()
        if post:
            post.actual_working_gp_lgd = vac_gp.lgd_code
            post.actual_working_mandal_id = vac_gp.mandal_id
            post.remarks += f" [Currently deployed to work in Clear Vacant GP: {vac_gp.gp_name}]"
    db.commit()
    print("Mapped 6 deputation employees to work in clear-vacant GPs.")

    print("=" * 70)
    print("TEST DATA SEEDING COMPLETE SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    run_seed()
