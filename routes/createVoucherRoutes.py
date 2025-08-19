from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from services.createVoucherService import TallyVoucherManager
from services.updateVoucherService import TallyVoucherUpdater
from services.transactionLedgerService import TallyLedgerFetcher
router = APIRouter()

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