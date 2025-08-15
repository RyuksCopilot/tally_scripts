from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.trialBalanceService import TallyTrialBalanceManager

router = APIRouter()

class TrialBalanceRequest(BaseModel):
    tally_url: str
    company_name: str

@router.post("/trial-balance")
def get_trial_balance(request: TrialBalanceRequest):
    try:
        manager = TallyTrialBalanceManager(request.tally_url)
        result = manager.get_trial_balance(request.dict(exclude={"tally_url"}))
        return {"message": "Trial balance fetched successfully", "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
