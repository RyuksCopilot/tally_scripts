from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from services.createLedgerService import TallyLedgerManager

router = APIRouter()

class LedgerRequest(BaseModel):
    tally_url: str
    company_name: str
    ledger_name: str
    group_name: str
    mailing_name: Optional[str] = None
    address_list: Optional[List[str]] = None
    pincode: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    opening_balance: Optional[str] = None

@router.post("/ledger/create")
def create_ledger(data: LedgerRequest):
    try:
        ledger_manager = TallyLedgerManager(data.tally_url)
        result = ledger_manager.save_ledger(data.dict(exclude={"tally_url"}), action="CREATE")
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        return {"message": "Ledger processed successfully", "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))