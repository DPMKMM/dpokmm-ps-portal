import os
import sys
import uvicorn
from app.config import settings
from app.database import engine, Base
from app.seed import seed_database

def main():
    print("=" * 80)
    print(" " * 15 + "GOVERNMENT OF TELANGANA - DISTRICT PANCHAYAT OFFICE")
    print(" " * 10 + settings.PROJECT_NAME.upper())
    print(" " * 28 + settings.SHORT_NAME)
    print("=" * 80)
    print(f"District: {settings.DISTRICT_NAME} | Mandals: {settings.TOTAL_MANDALS} | Gram Panchayats: {settings.TOTAL_GPS}")
    print("-" * 80)
    
    # 1. Initialize Tables & Seed Master Data
    print("Checking database schema and centralized master records...")
    Base.metadata.create_all(bind=engine)
    seed_database(force_reseed=False)
    
    print("-" * 80)
    print("ACCESS CREDENTIALS:")
    print("1. District Super Admin (All 571 GPs & 20 Mandals):")
    print("   Username: admin")
    print("   Password: Admin@Khammam2026")
    print("\n2. Mandal Admin Accounts (20 Mandals with Single Active Device Session Enforcement):")
    print("   Examples: enkoor, kallur, sathupally, penubally, thallada, mudigonda, khammam_rural")
    print("   Passwords: Mandal@<Mandal_LGD>  (e.g. Mandal@5065 for Enkoor, Mandal@5069 for Kallur)")
    print("\n3. District Viewer (Collectorate Read-Only Access):")
    print("   Username: viewer")
    print("   Password: Viewer@Khammam2026")
    print("-" * 80)
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting Web Application Server at: http://{host}:{port}")
    print("=" * 80)
    
    uvicorn.run("app.main:app", host=host, port=port, reload=False)

if __name__ == "__main__":
    main()
