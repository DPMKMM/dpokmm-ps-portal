from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, UserSession, LoginHistory, AuditLog
from app.schemas import (
    LoginRequest, TokenResponse, PasswordChangeRequest,
    ForceLogoutRequest, UserOut
)
from app.auth import (
    authenticate_and_create_session, get_current_user,
    require_super_admin, hash_password, verify_password
)
from app.config import settings

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    client_ip = request.client.host if request.client else "127.0.0.1"
    device_info = payload.device_info or request.headers.get("user-agent", "Unknown Device")
    
    return authenticate_and_create_session(
        username=payload.username.strip(),
        password=payload.password,
        ip_address=client_ip,
        device_info=device_info,
        db=db
    )

@router.post("/logout")
def logout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session_id = getattr(current_user, "current_session_id", None)
    now = datetime.utcnow()
    
    if session_id:
        sess = db.query(UserSession).filter(UserSession.session_id == session_id).first()
        if sess:
            sess.session_status = "TERMINATED"
            sess.logout_datetime = now
            
    # Record in history
    log = LoginHistory(
        user_id=current_user.id,
        username_attempted=current_user.username,
        ip_address="Session End",
        device_info="User Initiated Logout",
        status="LOGOUT",
        reason="Normal user logout"
    )
    db.add(log)
    
    audit = AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        mandal_id=current_user.mandal_id,
        action="LOGOUT",
        entity_type="SESSION",
        entity_id=session_id or str(current_user.id),
        details="User logged out successfully",
        timestamp=now
    )
    db.add(audit)
    db.commit()
    return {"message": "Logged out successfully"}

@router.post("/force-logout")
def force_logout(
    payload: ForceLogoutRequest,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db)
):
    now = datetime.utcnow()
    target_sessions = []
    
    if payload.session_id:
        target_sessions = db.query(UserSession).filter(
            UserSession.session_id == payload.session_id,
            UserSession.session_status == "ACTIVE"
        ).all()
    elif payload.username:
        user = db.query(User).filter(User.username == payload.username).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        target_sessions = db.query(UserSession).filter(
            UserSession.user_id == user.id,
            UserSession.session_status == "ACTIVE"
        ).all()
    else:
        raise HTTPException(status_code=400, detail="Must provide username or session_id")
        
    for s in target_sessions:
        s.session_status = "FORCE_LOGGED_OUT"
        s.logout_datetime = now
        
        # Log force logout
        hist = LoginHistory(
            user_id=s.user_id,
            username_attempted=s.user.username if s.user else "Unknown",
            ip_address=s.ip_address,
            device_info=s.device_info,
            status="FORCE_LOGOUT",
            reason=f"Force logged out by District Super Admin ({current_user.username})"
        )
        db.add(hist)
        
    audit = AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action="FORCE_LOGOUT",
        entity_type="SESSION",
        entity_id=payload.session_id or payload.username,
        details=f"Admin force-terminated {len(target_sessions)} active session(s)",
        timestamp=now
    )
    db.add(audit)
    db.commit()
    
    return {"message": f"Successfully terminated {len(target_sessions)} active session(s)"}

@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "display_name": current_user.display_name,
        "role": current_user.role,
        "mandal_id": current_user.mandal_id,
        "mandal_name": current_user.mandal.mandal_name if current_user.mandal else None,
        "mandal_lgd": current_user.mandal_lgd,
        "must_change_password": current_user.must_change_password,
        "session_id": getattr(current_user, "current_session_id", None)
    }

@router.post("/change-password")
def change_password(
    payload: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Current password does not match")
    if len(payload.new_password) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters")
        
    current_user.password_hash = hash_password(payload.new_password)
    current_user.must_change_password = False
    
    audit = AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        mandal_id=current_user.mandal_id,
        action="UPDATE_PASSWORD",
        entity_type="USER",
        entity_id=str(current_user.id),
        details="User successfully changed password",
        timestamp=datetime.utcnow()
    )
    db.add(audit)
    db.commit()
    return {"message": "Password updated successfully"}

@router.get("/active-sessions")
def get_active_sessions(
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db)
):
    now = datetime.utcnow()
    cutoff = now - timedelta(minutes=settings.SESSION_INACTIVITY_MINUTES)
    
    sessions = db.query(UserSession).filter(
        UserSession.session_status == "ACTIVE",
        UserSession.last_activity >= cutoff
    ).order_by(UserSession.login_datetime.desc()).all()
    
    results = []
    for s in sessions:
        u = s.user
        results.append({
            "session_id": s.session_id,
            "user_id": s.user_id,
            "username": u.username if u else "Unknown",
            "display_name": u.display_name if u else "Unknown",
            "role": u.role if u else "Unknown",
            "mandal_name": u.mandal.mandal_name if u and u.mandal else "All Mandals (District)",
            "login_datetime": s.login_datetime.strftime("%Y-%m-%d %H:%M:%S") if s.login_datetime else "",
            "last_activity": s.last_activity.strftime("%Y-%m-%d %H:%M:%S") if s.last_activity else "",
            "ip_address": s.ip_address,
            "device_info": s.device_info,
            "session_status": s.session_status
        })
    return results

@router.get("/login-history")
def get_login_history(
    limit: int = 100,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db)
):
    histories = db.query(LoginHistory).order_by(LoginHistory.created_at.desc()).limit(limit).all()
    return [
        {
            "id": h.id,
            "username_attempted": h.username_attempted,
            "ip_address": h.ip_address,
            "device_info": h.device_info,
            "status": h.status,
            "reason": h.reason,
            "created_at": h.created_at.strftime("%Y-%m-%d %H:%M:%S") if h.created_at else ""
        }
        for h in histories
    ]
