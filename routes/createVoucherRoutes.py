from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional,List
from services.createVoucherService import TallyVoucherManager
from services.updateVoucherService import TallyVoucherUpdater
from services.transactionLedgerService import TallyLedgerFetcher
from services.createInventoryVoucherService import TallyInventoryVoucherManager
from services.inventorySalesVoucherService import TallySalesVoucherManager

router = APIRouter()


class Item(BaseModel):
    name: str
    qty: float
    rate: float
    unit: str

class SalesVoucherRequest(BaseModel):
    tally_url: str = "http://localhost:9000"
    company_name: str
    customer_ledger: str
    sales_ledger: str
    items: list[Item]
    date: str  # Format YYYYMMDD
    narration: str | None = None


@router.post("/create-sales-voucher")
def create_sales_voucher(request: SalesVoucherRequest):
    try:
        sales_manager = TallySalesVoucherManager(request.tally_url)
        data = {
            "company_name": request.company_name,
            "customer_ledger": request.customer_ledger,
            "sales_ledger": request.sales_ledger,
            "items": [item.dict() for item in request.items],
            "date": request.date,
            "narration": request.narration,
        }

        result = sales_manager.save_voucher(data, action="Create")
        return {"message": "Sales voucher created successfully", "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class InventoryItem(BaseModel):
    name: str
    qty: float
    rate: float
    unit: str


class InventoryVoucherRequest(BaseModel):
    tally_url: str
    company_name: str
    party_ledger: str
    purchase_ledger: str
    items: List[InventoryItem]
    date: str  # YYYYMMDD
    narration: Optional[str] = None
    voucher_type: str = "Purchase"
    voucher_guid: Optional[str] = None


@router.post("/voucher/purchase-inventory/create")
def create_inventory_voucher(request: InventoryVoucherRequest):
    try:
        inventory_manager = TallyInventoryVoucherManager(request.tally_url)
        result = inventory_manager.save_voucher(request.dict(exclude={"tally_url"}), action="Create")
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        return {"message": "Inventory Purchase Voucher processed successfully", "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class VoucherRequest(BaseModel):
    tally_url: str
    company_name: str
    from_ledger: str
    to_ledger: str
    amount: float
    voucher_type: str
    date: str  # Format: YYYYMMDD
    narration: Optional[str] = None
    voucher_guid: Optional[str] = None

@router.post("/voucher/create")
def create_voucher(data: VoucherRequest):
    try:
        voucher_manager = TallyVoucherManager(data.tally_url)
        result = voucher_manager.save_voucher(data.dict(exclude={"tally_url"}), action="Create")
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        return {"message": "Voucher processed successfully", "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    
class VoucherData(BaseModel):
    company_name: Optional[str] = None
    from_ledger: Optional[str] = None
    to_ledger: Optional[str] = None
    amount: Optional[float] = None
    voucher_type: Optional[str] = None
    date: Optional[str] = None
    narration: Optional[str] = None

class VoucherUpdateRequest(BaseModel):
    tally_url: str
    old_voucher: VoucherData
    new_voucher: VoucherData
    
    
@router.post("/voucher/update")
def update_voucher(request: VoucherUpdateRequest):
    try:
        updater = TallyVoucherUpdater(tally_url=request.tally_url)
        result = updater.update_voucher(
            old_lookup=request.old_voucher.dict(),
            new_data=request.new_voucher.dict()
        )
        return {"status": "success", "details": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
class VoucherDeleteRequest(BaseModel):
    tally_url: str
    old_voucher: VoucherData
    

@router.post("/voucher/delete")
def delete_voucher(request: VoucherDeleteRequest):
    try:
        updater = TallyVoucherUpdater(tally_url=request.tally_url)
        result = updater.delete_voucher(
            old_lookup=request.old_voucher.dict()
        )
        return {"status": "success", "details": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class VoucherTransactionsRequest(BaseModel):
    tally_url: str
    company_name: str
    ledger_name :str
    

@router.post("/voucher/transactions")
def get_voucher_transactions(request: VoucherTransactionsRequest):
    try:
        fetcher = TallyLedgerFetcher(tally_url=request.tally_url)
        result = fetcher.get_ledger_transactions(
            company_name=request.company_name,
            ledger_name=request.ledger_name
        )
        return {"status": "success", "details": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))