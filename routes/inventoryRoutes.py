from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from services.inventoryService import TallyInventoryManagement  
router = APIRouter()

class StockItemRequest(BaseModel):
    tally_url: str
    company_name: str
    item_name: str
    parent_group: str
    unit: str
    opening_balance: Optional[float] = 0

@router.post("/inventory/item/create")
def create_stock_item(request: StockItemRequest):
    try:
        manager = TallyInventoryManagement(request.tally_url)
        result = manager.create_stock_item(
            company_name=request.company_name,
            item_name=request.item_name,
            parent_group=request.parent_group,
            unit=request.unit,
            opening_balance=request.opening_balance
        )
        return {"message": "Stock Item created successfully", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class StockJournalRequest(BaseModel):
    tally_url: str
    company_name: str
    narration: str
    item_name: str
    qty: float
    unit: str
    godown: Optional[str] = "Main Location"
    date: str  # YYYYMMDD
    voucher_guid: Optional[str] = None

@router.post("/inventory/journal/create")
def create_stock_journal(request: StockJournalRequest):
    try:
        manager = TallyInventoryManagement(request.tally_url)
        result = manager.create_stock_journal(
            company_name=request.company_name,
            narration=request.narration,
            item_name=request.item_name,
            qty=request.qty,
            unit=request.unit,
            godown=request.godown,
            date=request.date
        )
        return {"message": "Stock Journal created successfully", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
