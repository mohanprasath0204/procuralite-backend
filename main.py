from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware # <--- ADD THIS LINE
from fastapi.responses import Response
from typing import List
import models
import schemas
import io
import csv
from fastapi.responses import Response
from database import engine, get_db

models.Base.metadata.create_all(bind=engine)
app = FastAPI(title="ProcuraLite OS", version="1.0")

app = FastAPI(title="ProcuraLite OS", version="1.0")

# ==========================================
# CORS SECURITY WHITELIST
# ==========================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], # Tells Python to trust your Next.js dashboard
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check(): return {"status": "System Online"}

# VENDOR APIs
@app.post("/api/v1/vendors", response_model=schemas.VendorResponse)
def create_vendor(vendor: schemas.VendorCreate, db: Session = Depends(get_db)):
    if db.query(models.Vendor).filter(models.Vendor.email == vendor.email).first(): raise HTTPException(status_code=400, detail="Email exists.")
    if db.query(models.Vendor).filter(models.Vendor.gstin == vendor.gstin).first(): raise HTTPException(status_code=400, detail="GSTIN exists.")
    new_vendor = models.Vendor(**vendor.model_dump())
    db.add(new_vendor)
    db.commit()
    db.refresh(new_vendor)
    return new_vendor

# MATERIAL APIs
@app.post("/api/v1/materials", response_model=schemas.MaterialResponse)
def create_material(material: schemas.MaterialCreate, db: Session = Depends(get_db)):
    if db.query(models.Material).filter(models.Material.mat_id == material.mat_id).first(): raise HTTPException(status_code=400, detail="ID exists.")
    new_material = models.Material(**material.model_dump())
    db.add(new_material)
    db.commit()
    db.refresh(new_material)
    return new_material

# PR APIs
@app.post("/api/v1/requisitions", response_model=schemas.PRResponse)
def create_requisition(pr: schemas.PRCreate, db: Session = Depends(get_db)):
    if not db.query(models.Material).filter(models.Material.mat_id == pr.mat_id).first(): raise HTTPException(status_code=404, detail="Material not found.")
    new_pr = models.PurchaseRequisition(**pr.model_dump())
    db.add(new_pr)
    db.commit()
    db.refresh(new_pr)
    return new_pr

# PO APIs
@app.post("/api/v1/orders", response_model=schemas.POResponse)
def create_order(po: schemas.POCreate, db: Session = Depends(get_db)):
    # 1. Quality Control: Does PR exist?
    pr_record = db.query(models.PurchaseRequisition).filter(models.PurchaseRequisition.pr_id == po.pr_id).first()
    if not pr_record:
        raise HTTPException(status_code=404, detail="Purchase Requisition ID not found.")
    
    # 2. Quality Control: Does Vendor exist?
    if not db.query(models.Vendor).filter(models.Vendor.vendor_id == po.vendor_id).first():
        raise HTTPException(status_code=404, detail="Vendor ID not found.")

    new_po = models.PurchaseOrder(**po.model_dump())
    
    # ADVANCED FEATURE: Automatically update PR status when PO is created!
    pr_record.status = "PO Created"
    
    db.add(new_po)
    db.commit()
    db.refresh(new_po)
    return new_po




# ==========================================
# GRN APIs (RECEIVING)
# ==========================================
@app.post("/api/v1/receipts", response_model=schemas.GRNResponse)
def create_receipt(grn: schemas.GRNCreate, db: Session = Depends(get_db)):
    # 1. Check if the Purchase Order exists
    po_record = db.query(models.PurchaseOrder).filter(models.PurchaseOrder.po_id == grn.po_id).first()
    if not po_record:
        raise HTTPException(status_code=404, detail="Purchase Order not found.")
    
    # 2. Save the GRN
    new_grn = models.GoodsReceipt(**grn.model_dump())
    db.add(new_grn)
    
    # 3. ADVANCED LEAN OPERATION: Automatically update PO status based on delivery!
    if grn.received_qty >= po_record.order_qty:
        po_record.status = "Fully Received"
    elif grn.received_qty > 0:
        po_record.status = "Partially Received"
        
    db.commit()
    db.refresh(new_grn)
    return new_grn




# ==========================================
# INVOICE & 3-WAY MATCH APIs
# ==========================================
@app.post("/api/v1/invoices", response_model=schemas.InvoiceResponse)
def create_and_match_invoice(invoice: schemas.InvoiceCreate, db: Session = Depends(get_db)):
    # 1. Find the original PO
    po_record = db.query(models.PurchaseOrder).filter(models.PurchaseOrder.po_id == invoice.po_id).first()
    if not po_record:
        raise HTTPException(status_code=404, detail="Purchase Order not found.")
        
    # 2. Find the GRN for this PO
    grn_record = db.query(models.GoodsReceipt).filter(models.GoodsReceipt.po_id == invoice.po_id).first()
    if not grn_record:
        raise HTTPException(status_code=400, detail="Cannot process invoice: No GRN found for this PO.")

    # 3. THE 3-WAY MATCH ALGORITHM
    match_status = "CLEARED"
    variances = []

    # Check 1: Quantity Match (Billed vs. Actually Accepted)
    if invoice.billed_qty > grn_record.received_qty:
        match_status = "EXCEPTION"
        variances.append(f"Qty Variance: Billed {invoice.billed_qty}, but only accepted {grn_record.received_qty}.")
        
    # Check 2: Price Match (Billed vs. PO Agreement)
    if invoice.billed_price > po_record.unit_price:
        match_status = "EXCEPTION"
        variances.append(f"Price Variance: Billed at {invoice.billed_price}, PO was {po_record.unit_price}.")

    # 4. Save the Invoice with the results
    variance_string = " | ".join(variances) if variances else "Perfect Match"
    
    new_invoice = models.Invoice(
        inv_id=invoice.inv_id,
        po_id=invoice.po_id,
        vendor_inv_num=invoice.vendor_inv_num,
        billed_qty=invoice.billed_qty,
        billed_price=invoice.billed_price,
        match_status=match_status,
        variance_notes=variance_string
    )
    
    db.add(new_invoice)
    db.commit()
    db.refresh(new_invoice)
    return new_invoice






# ==========================================
# ANALYTICS APIs (THE DASHBOARD DATA)
# ==========================================
@app.get("/api/v1/analytics/spend", response_model=schemas.SpendAnalytics)
def get_spend_analytics(db: Session = Depends(get_db)):
    # 1. Calculate Total Spend (Sum of all PO quantities * PO unit price)
    all_pos = db.query(models.PurchaseOrder).all()
    total_spend = sum([po.order_qty * po.unit_price for po in all_pos])
    
    # 2. Count Flagged Invoices
    flagged_invoices = db.query(models.Invoice).filter(models.Invoice.match_status == "EXCEPTION").count()
    
    return {
        "total_spend": total_spend,
        "total_pos_issued": len(all_pos),
        "total_invoices_flagged": flagged_invoices
    }

@app.get("/api/v1/analytics/suppliers/{vendor_id}", response_model=schemas.SupplierScorecard)
def get_supplier_scorecard(vendor_id: str, db: Session = Depends(get_db)):
    # 1. Find the Vendor
    vendor = db.query(models.Vendor).filter(models.Vendor.vendor_id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found.")

    # 2. Get all POs for this specific vendor
    vendor_pos = db.query(models.PurchaseOrder).filter(models.PurchaseOrder.vendor_id == vendor_id).all()
    po_ids = [po.po_id for po in vendor_pos]
    
    # 3. Calculate Total Rejected Items from GRNs linked to these POs
    grns = db.query(models.GoodsReceipt).filter(models.GoodsReceipt.po_id.in_(po_ids)).all()
    total_rejected = sum([grn.rejected_qty for grn in grns])
    
    # 4. Calculate Total Flagged Invoices for this vendor
    flagged_invoices = db.query(models.Invoice).filter(models.Invoice.po_id.in_(po_ids), models.Invoice.match_status == "EXCEPTION").count()

    return {
        "vendor_name": vendor.vendor_name,
        "total_orders": len(vendor_pos),
        "items_rejected": total_rejected,
        "invoices_flagged": flagged_invoices
    }




# ==========================================
# 8. EXCEL / CSV EXPORT API
# ==========================================
@app.get("/api/v1/export/invoices")
def export_invoices_csv(db: Session = Depends(get_db)):
    # 1. Get all invoices from the database
    invoices = db.query(models.Invoice).all()
    
    # 2. Create an empty Excel/CSV file in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # 3. Write the Header Row
    writer.writerow(["Invoice ID", "PO ID", "Billed Qty", "Billed Price", "Match Status", "Variances"])
    
    # 4. Write the Data Rows
    for inv in invoices:
        writer.writerow([
            inv.inv_id, 
            inv.po_id, 
            inv.billed_qty, 
            inv.billed_price, 
            inv.match_status, 
            inv.variance_notes
        ])
    
    # 5. Package it as a downloadable file
    return Response(
        content=output.getvalue(), 
        media_type="text/csv", 
        headers={"Content-Disposition": "attachment; filename=invoice_audit_report.csv"}
    )