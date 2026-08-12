from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, ForeignKey
from datetime import datetime, timezone
from database import Base

# ==========================================
# 1. MATERIALS MASTER
# ==========================================
class Material(Base):
    __tablename__ = "materials"
    
    material_id = Column(String(20), primary_key=True, index=True)
    description = Column(String(255), nullable=False)
    category = Column(String(50), nullable=False)
    unit_of_measure = Column(String(10), nullable=False)
    standard_price = Column(Float, nullable=False)
    minimum_order_qty = Column(Integer, default=1)
    storage_bin = Column(String(50))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

# ==========================================
# 2. VENDORS MASTER
# ==========================================
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

# ==========================================
# 3. PURCHASE REQUISITIONS (INTERNAL)
# ==========================================
class PurchaseRequisition(Base):
    __tablename__ = "purchase_requisitions"
    
    pr_id = Column(String(20), primary_key=True, index=True)
    requester_name = Column(String(100), nullable=False)
    material_id = Column(String(20), ForeignKey("materials.material_id"), nullable=False)
    requested_qty = Column(Integer, nullable=False)
    status = Column(String(20), default="Pending")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

# ==========================================
# 4. PURCHASE ORDERS (EXTERNAL)
# ==========================================
class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"
    
    po_id = Column(String(20), primary_key=True, index=True)
    pr_id = Column(String(20), ForeignKey("purchase_requisitions.pr_id"), nullable=False)
    vendor_id = Column(String(20), ForeignKey("vendors.vendor_id"), nullable=False)
    order_qty = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    status = Column(String(20), default="Sent") 
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

# ==========================================
# 5. GOODS RECEIPTS (LOGISTICS)
# ==========================================
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
