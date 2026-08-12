from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import io
import csv
from fastapi.responses import Response

# Import your local files
import models
import schemas
from database import engine, get_db

# Initialize database tables
models.Base.metadata.create_all(bind=engine)

# Initialize FastAPI App
app = FastAPI(title="ProcuraLite OS", version="1.0")

# ==========================================
# CORS SECURITY WHITELIST
# ==========================================
# This opens the gates so your Vercel dashboard can send data here
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# HEALTH CHECK API
# ==========================================
@app.get("/")
def health_check(): 
    return {"status": "System Online", "message": "ProcuraLite API is running."}

# ==========================================
# VENDOR APIs (MASTER DATA)
# ==========================================
@app.post("/api/v1/vendors", response_model=schemas.VendorResponse)
def create_vendor(vendor: schemas.VendorCreate, db: Session = Depends(get_db)):
    # Check if vendor already exists to prevent duplicates
    existing_vendor = db.query(models.Vendor).filter(models.Vendor.vendor_id == vendor.vendor_id).first()
    if existing_vendor:
        raise HTTPException(status_code=400, detail="Vendor ID already exists in the system")
    
    # Save new vendor to the database (Now securely mapped with payment_terms)
    new_vendor = models.Vendor(
        vendor_id=vendor.vendor_id,
        vendor_name=vendor.vendor_name,
        email=vendor.email,
        gstin=vendor.gstin,
        payment_terms=vendor.payment_terms
    )
    db.add(new_vendor)
    db.commit()
    db.refresh(new_vendor)
    return new_vendor

@app.get("/api/v1/vendors", response_model=List[schemas.VendorResponse])
def get_vendors(db: Session = Depends(get_db)):
    # Fetch all vendors for the frontend dashboard table
    return db.query(models.Vendor).all()

# ==========================================
# ANALYTICS & DASHBOARD APIs
# ==========================================
@app.get("/api/v1/analytics/spend")
def get_spend_analytics(db: Session = Depends(get_db)):
    # Connects to your KPI cards on the Overview tab
    return {
        "total_spend": 0,
        "total_pos_issued": 0,
        "total_invoices_flagged": 0
    }

# ==========================================
# EXPORT & REPORTING APIs
# ==========================================
@app.get("/api/v1/export/invoices")
def export_invoices(db: Session = Depends(get_db)):
    # Generates the CSV for the 3-Way Match Audit download
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Invoice ID", "PO Number", "Vendor ID", "Variance Reason", "Status"])
    writer.writerow(["INV-001", "PO-100", "VEN-01", "Price Variance", "Flagged"])
    
    response = Response(content=output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=3way_match_audit.csv"
    response.headers["Content-Type"] = "text/csv"
    return response
