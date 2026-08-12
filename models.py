from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, ForeignKey
from datetime import datetime, timezone
from database import Base

class Material(Base):
    __tablename__ = "materials"
    mat_id = Column(String(20), primary_key=True, index=True)
    mat_description = Column(String(255), nullable=False)
    material_type = Column(String(10), nullable=False) 
    base_uom = Column(String(10), nullable=False)
    standard_price = Column(Float, nullable=False)
    minimum_order_qty = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Vendor(Base):
    __tablename__ = "vendors"
    vendor_id = Column(String(20), primary_key=True, index=True)
    vendor_name = Column(String(150), nullable=False)
    contact_person = Column(String(100))
    email = Column(String(100), unique=True, index=True, nullable=False)
    phone = Column(String(20))
    gstin = Column(String(15), unique=True, nullable=False)
    payment_terms = Column(String(50), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    from sqlalchemy import Float # Add this at the top of the file if it is missing

class Material(Base):
    __tablename__ = "materials"

    material_id = Column(String, primary key=True, index=True)
    description = Column(String, index=True)
    category = Column(String)
    unit_of_measure = Column(String)
    standard_price = Column(Float)
    storage_bin = Column(String)

class PurchaseRequisition(Base):
    __tablename__ = "purchase_requisitions"
    pr_id = Column(String(20), primary_key=True, index=True)
    requester_name = Column(String(100), nullable=False)
    mat_id = Column(String(20), ForeignKey("materials.mat_id"), nullable=False)
    requested_qty = Column(Integer, nullable=False)
    status = Column(String(20), default="Pending")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"
    po_id = Column(String(20), primary_key=True, index=True)
    pr_id = Column(String(20), ForeignKey("purchase_requisitions.pr_id"), nullable=False)
    vendor_id = Column(String(20), ForeignKey("vendors.vendor_id"), nullable=False)
    order_qty = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    status = Column(String(20), default="Sent") 
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class GoodsReceipt(Base):
    __tablename__ = "goods_receipts"
    grn_id = Column(String(20), primary_key=True, index=True)
    po_id = Column(String(20), ForeignKey("purchase_orders.po_id"), nullable=False)
    received_qty = Column(Integer, nullable=False)
    rejected_qty = Column(Integer, default=0)
    rejection_reason = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

# ==========================================
# 6. INVOICE TABLE (3-WAY MATCH)
# ==========================================
class Invoice(Base):
    __tablename__ = "invoices"
    inv_id = Column(String(20), primary_key=True, index=True)
    po_id = Column(String(20), ForeignKey("purchase_orders.po_id"), nullable=False)
    vendor_inv_num = Column(String(50), nullable=False)
    billed_qty = Column(Integer, nullable=False)
    billed_price = Column(Float, nullable=False)
    
    # This is the magic column. It will say "CLEARED" or "EXCEPTION"
    match_status = Column(String(20), default="Pending")
    variance_notes = Column(String(255), nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
