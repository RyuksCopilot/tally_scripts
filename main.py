from fastapi import FastAPI
from routes.createLedgerRoutes import router as ledger_router
from routes.trialBalanceRoutes import router as trial_balance_router
from routes.createVoucherRoutes import router as voucher_router

app = FastAPI()

app.include_router(ledger_router, prefix="/api", tags=["Ledger Management"])
app.include_router(trial_balance_router, prefix="/api", tags=["Trial Balance"])
app.include_router(voucher_router, prefix="/api", tags=["Voucher Management"])

@app.get("/")
def root():
    return {"message": "Tally API is running"}