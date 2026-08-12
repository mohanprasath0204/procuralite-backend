from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

# 1. MATERIAL SCHEMAS
class MaterialBase(BaseModel):
    mat_id: str = Field(..., max_length=20)
    mat_description: str = Field(..., max_length=255)
    material_type: str = Field(..., pattern="^(ROH|HALB|FERT)$")
    base_uom: str = Field(..., max_length=10)
    standard_price: float = Field(..., gt=0)
    minimum_order_qty: int = Field(default=1, gt=0)

class MaterialCreate(MaterialBase): pass

class MaterialResponse(MaterialBase):
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# 2. VENDOR SCHEMAS
class VendorBase(BaseModel):
    vendor_id: str = Field(..., max_length=20)
    vendor_name: str = Field(..., max_length=150)
    contact_person: Optional[str] = Field(None, max_length=100)
    email: str = Field(...)
    phone: Optional[str] = Field(None, max_length=20)
    gstin: str = Field(..., pattern="^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$")
    payment_terms: str = Field(..., max_length=50)

class VendorCreate(VendorBase): pass

class VendorResponse(VendorBase):
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# 3. PR SCHEMAS
class PRBase(BaseModel):
    pr_id: str = Field(..., max_length=20)
    requester_name: str = Field(..., max_length=100)
    mat_id: str
    requested_qty: int = Field(..., gt=0)

class PRCreate(PRBase): pass

class PRResponse(PRBase):
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# 4. PO SCHEMAS
class POBase(BaseModel):
    po_id: str = Field(..., max_length=20)
    pr_id: str
    vendor_id: str
    order_qty: int = Field(..., gt=0)
    unit_price: float = Field(..., gt=0)

class POCreate(POBase): pass

class POResponse(POBase):
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
    # ==========================================
# 5. GRN SCHEMAS
# ==========================================
class GRNBase(BaseModel):
    grn_id: str = Field(..., max_length=20)
    po_id: str
    received_qty: int = Field(..., ge=0, description="Quantity accepted")
    rejected_qty: int = Field(default=0, ge=0, description="Quantity failed QA")
    rejection_reason: Optional[str] = None

class GRNCreate(GRNBase): pass

class GRNResponse(GRNBase):
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)







    # ==========================================
# 6. INVOICE SCHEMAS
# ==========================================
class InvoiceBase(BaseModel):
    inv_id: str = Field(..., max_length=20)
    po_id: str
    vendor_inv_num: str = Field(..., max_length=50)
    billed_qty: int = Field(..., gt=0)
    billed_price: float = Field(..., gt=0)

class InvoiceCreate(InvoiceBase): pass

class InvoiceResponse(InvoiceBase):
    match_status: str
    variance_notes: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)




    # ==========================================
# 7. ANALYTICS SCHEMAS
# ==========================================
class SpendAnalytics(BaseModel):
    total_spend: float
    total_pos_issued: int
    total_invoices_flagged: int

class SupplierScorecard(BaseModel):
    vendor_name: str
    total_orders: int
    items_rejected: int
    invoices_flagged: int


# ==========================================
# MATERIAL SCHEMAS
# ==========================================
class MaterialCreate(BaseModel):
    material_id: str
    description: str
    category: str
    unit_of_measure: str
    standard_price: float
    storage_bin: str

class MaterialResponse(MaterialCreate):
    class Config:
        from_attributes = True
