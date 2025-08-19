from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.balanceSheetService import TallyBalanceSheetFetcher

router = APIRouter()

class BalanceSheetRequest(BaseModel):
    tally_url: str
    company_name: str

@router.post("/balance-sheet")
def get_balance_sheet(request: BalanceSheetRequest):
    try:
        balancesheetmanager = TallyBalanceSheetFetcher(request.tally_url)
        result = balancesheetmanager.get_balance_sheet(company_name=request.company_name)
        return {"message": "Balance Sheet fetched successfully", "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))