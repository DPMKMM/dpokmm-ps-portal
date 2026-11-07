import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, Base
from app.seed import seed_database

# Import routers
from app.routers import (
    auth_router,
    gp_router,
    employee_router,
    deputation_router,
    verification_router,
    discrepancy_router,
    analytics_router,
    reports_router,
    import_export_router,
    admin_router,
    document_router
)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Panchayat Secretary Posting, Deputation, Salary Mapping and Employee Availability Management System - District Panchayat Office, Khammam, Telangana",
    version="2.0.0"
)

# CORS configuration for panchayatautomation.in and dpokmm subdomain
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://www.panchayatautomation.in",
        "https://panchayatautomation.in",
        "https://www.dpokmm.panchayatautomation.in",
        "https://dpokmm.panchayatautomation.in",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers at root /api
all_routers = [
    auth_router.router,
    gp_router.router,
    employee_router.router,
    deputation_router.router,
    verification_router.router,
    discrepancy_router.router,
    analytics_router.router,
    reports_router.router,
    import_export_router.router,
    admin_router.router,
    document_router.router
]

for r in all_routers:
    app.include_router(r)
    # Support both /ps-data and /psdata prefixes seamlessly
    app.include_router(r, prefix="/ps-data")
    app.include_router(r, prefix="/psdata")

# Mount Static Files at /static, /ps-data/static, and /psdata/static
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    app.mount("/ps-data/static", StaticFiles(directory=static_dir), name="ps_data_static")
    app.mount("/psdata/static", StaticFiles(directory=static_dir), name="psdata_static")

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    seed_database(force_reseed=False)

@app.get("/health")
@app.get("/api/health")
@app.get("/ps-data/api/health")
@app.get("/psdata/api/health")
def health_check():
    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "short_name": settings.SHORT_NAME,
        "department": settings.DEPARTMENT,
        "district": settings.DISTRICT_NAME,
        "total_mandals": settings.TOTAL_MANDALS,
        "total_gps": settings.TOTAL_GPS
    }

@app.get("/", response_class=HTMLResponse)
@app.get("/ps-data", response_class=HTMLResponse)
@app.get("/ps-data/", response_class=HTMLResponse)
@app.get("/psdata", response_class=HTMLResponse)
@app.get("/psdata/", response_class=HTMLResponse)
async def serve_index():
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return "<h1>Details of Panchayat Secretaries Working in Khammam District</h1><p>Frontend initializing...</p>"
