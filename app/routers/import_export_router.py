import io
from datetime import datetime, date
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment

from app.database import get_db
from app.models import (
    GramPanchayat, Mandal, Employee, EmployeeSalaryMapping,
    EmployeePosting, EmployeeStatusHistory, User, AuditLog
)
from app.auth import get_current_user, require_super_admin

router = APIRouter(prefix="/api/import-export", tags=["Bulk Excel Import & Export"])

@router.get("/template")
def download_employee_template():
    """
    Downloads standard Excel template for employee data collection.
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Employee_Data_Template"
    
    headers = [
        "Employee ID (Mandatory Unique)",
        "Employee Name as per IFMIS",
        "Mobile Number (10 Digits)",
        "Date of Birth (YYYY-MM-DD)",
        "Salary Claiming GP LGD Code",
        "Working in Salary GP? (YES / NO)",
        "Posting Type (OWN_GP / WITHIN_MANDAL / ANOTHER_MANDAL / OTHER_DISTRICT)",
        "Actual Working GP LGD Code (if Khammam)",
        "External District Name (if Other District)",
        "External Mandal Name",
        "External Office / GP Name",
        "Deputation Order Number",
        "Deputation Order Date (YYYY-MM-DD)",
        "Service Status (WORKING / SUSPENDED / ABSCONDING / LEAVE)",
        "Expected Joining Date (YYYY-MM-DD)",
        "Remarks"
    ]
    
    header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    
    for col_idx, h in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col_idx, value=h)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        col_letter = openpyxl.utils.get_column_letter(col_idx)
        ws.column_dimensions[col_letter].width = max(len(h) + 2, 22)
        
    # Sample row
    sample_row = [
        "TS-99001",
        "K. V. Subba Rao",
        "9848012345",
        "1990-05-15",
        202319,
        "YES",
        "OWN_GP",
        "",
        "",
        "",
        "",
        "",
        "",
        "WORKING",
        "",
        "Verified with service register"
    ]
    ws.append(sample_row)
    ws.row_dimensions[1].height = 30
    ws.row_dimensions[2].height = 20
    
    stream = io.BytesIO()
    wb.save(stream)
    stream.seek(0)
    
    return StreamingResponse(
        stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=Panchayat_Secretary_Upload_Template.xlsx"}
    )

@router.post("/upload-employees")
async def upload_employees_excel(
    file: UploadFile = File(...),
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db)
):
    """
    SECTION 18: BULK EXCEL IMPORT ENGINE WITH VALIDATION REPORTING
    """
    if not file.filename.endswith((".xlsx", ".xlsm")):
        raise HTTPException(status_code=400, detail="Only Excel files (.xlsx) are supported")
        
    content = await file.read()
    try:
        wb = openpyxl.load_workbook(io.BytesIO(content), data_only=True)
        ws = wb.active
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read Excel workbook: {str(e)}")
        
    rows = list(ws.iter_rows(values_only=True))[1:] # Skip header
    total_rows = len(rows)
    success_count = 0
    duplicate_count = 0
    invalid_gp_count = 0
    error_list = []
    
    now = datetime.utcnow()
    
    for row_num, row in enumerate(rows, start=2):
        if not row or not any(row):
            continue
            
        emp_id = str(row[0]).strip() if row[0] else None
        name = str(row[1]).strip() if row[1] else None
        
        # Check if row has 16 columns (with mobile) or 15 columns (without)
        if len(row) >= 16:
            mobile_val = str(row[2]).strip() if row[2] else None
            dob_val = row[3]
            salary_lgd_raw = row[4]
            working_in_own_raw = str(row[5]).strip().upper() if len(row) > 5 and row[5] else "YES"
            posting_type_raw = str(row[6]).strip() if len(row) > 6 and row[6] else "OWN_GP"
            working_lgd_raw = row[7] if len(row) > 7 else None
            ext_district = str(row[8]).strip() if len(row) > 8 and row[8] else None
            service_status = str(row[13]).strip().upper() if len(row) > 13 and row[13] else "WORKING"
        else:
            mobile_val = None
            dob_val = row[2]
            salary_lgd_raw = row[3]
            working_in_own_raw = str(row[4]).strip().upper() if len(row) > 4 and row[4] else "YES"
            posting_type_raw = str(row[5]).strip() if len(row) > 5 and row[5] else "OWN_GP"
            working_lgd_raw = row[6] if len(row) > 6 else None
            ext_district = str(row[7]).strip() if len(row) > 7 and row[7] else None
            service_status = str(row[12]).strip().upper() if len(row) > 12 and row[12] else "WORKING"
        
        # Validation 1: Required fields
        if not emp_id or not name:
            error_list.append({
                "row": row_num,
                "employee_id": emp_id or "N/A",
                "error": "Missing mandatory Employee ID or Employee Name"
            })
            continue
            
        # Validation 2: Global Employee ID duplicate check
        existing_emp = db.query(Employee).filter(Employee.employee_id == emp_id).first()
        if existing_emp:
            duplicate_count += 1
            error_list.append({
                "row": row_num,
                "employee_id": emp_id,
                "error": f"Employee ID {emp_id} already exists in the district database"
            })
            continue
            
        # Validation 3: Salary GP validation
        try:
            salary_lgd = int(salary_lgd_raw)
        except (ValueError, TypeError):
            invalid_gp_count += 1
            error_list.append({
                "row": row_num,
                "employee_id": emp_id,
                "error": f"Invalid Salary GP LGD Code: {salary_lgd_raw}"
            })
            continue
            
        salary_gp = db.query(GramPanchayat).filter(GramPanchayat.lgd_code == salary_lgd).first()
        if not salary_gp:
            invalid_gp_count += 1
            error_list.append({
                "row": row_num,
                "employee_id": emp_id,
                "error": f"Salary GP LGD Code {salary_lgd} does not exist in centralized GP Master"
            })
            continue
            
        # Parse DOB
        dob_date = None
        if isinstance(dob_val, (datetime, date)):
            dob_date = dob_val if isinstance(dob_val, date) else dob_val.date()
        elif isinstance(dob_val, str):
            try:
                dob_date = datetime.strptime(dob_val.strip(), "%Y-%m-%d").date()
            except ValueError:
                dob_date = date(1990, 1, 1)
        else:
            dob_date = date(1990, 1, 1)
            
        # Working GP / Deputation details
        is_own = (working_in_own_raw == "YES")
        act_gp_lgd = salary_lgd if is_own else None
        act_mandal_id = salary_gp.mandal_id if is_own else None
        
        if not is_own and working_lgd_raw:
            try:
                w_lgd = int(working_lgd_raw)
                w_gp = db.query(GramPanchayat).filter(GramPanchayat.lgd_code == w_lgd).first()
                if w_gp:
                    act_gp_lgd = w_gp.lgd_code
                    act_mandal_id = w_gp.mandal_id
            except (ValueError, TypeError):
                pass
                
        # Insert
        try:
            emp = Employee(
                employee_id=emp_id,
                name_ifmis=name,
                dob=dob_date,
                mobile_number=mobile_val,
                created_by=f"Bulk Import ({current_user.username})",
                created_at=now
            )
            db.add(emp)
            db.flush()
            
            s_map = EmployeeSalaryMapping(
                employee_id=emp_id,
                salary_gp_lgd=salary_gp.lgd_code,
                salary_mandal_id=salary_gp.mandal_id,
                effective_from=date.today(),
                is_active=True,
                created_by=current_user.username,
                created_at=now
            )
            db.add(s_map)
            
            posting = EmployeePosting(
                employee_id=emp_id,
                is_working_in_salary_gp=is_own,
                posting_type=posting_type_raw if not is_own else "OWN_GP",
                actual_working_gp_lgd=act_gp_lgd,
                actual_working_mandal_id=act_mandal_id,
                external_district_name=ext_district,
                verification_status="VERIFIED_BOTH" if is_own else "PENDING",
                is_current=True,
                updated_by=current_user.username,
                created_at=now,
                updated_at=now
            )
            db.add(posting)
            
            st_hist = EmployeeStatusHistory(
                employee_id=emp_id,
                service_status=service_status,
                status_effective_from=date.today(),
                is_current=True,
                updated_by=current_user.username,
                updated_at=now
            )
            db.add(st_hist)
            success_count += 1
        except Exception as ex:
            error_list.append({
                "row": row_num,
                "employee_id": emp_id,
                "error": f"Database insertion error: {str(ex)}"
            })
            
    db.commit()
    
    # Audit log
    audit = AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action="BULK_IMPORT",
        entity_type="EMPLOYEE",
        details=f"Imported {success_count} employees. Errors: {len(error_list)}. Duplicates: {duplicate_count}",
        timestamp=now
    )
    db.add(audit)
    db.commit()
    
    return {
        "total_rows_processed": total_rows,
        "successfully_imported": success_count,
        "duplicate_employee_ids": duplicate_count,
        "invalid_gp_codes": invalid_gp_count,
        "total_errors": len(error_list),
        "errors": error_list[:100] # Top 100 errors for UI inspection
    }
