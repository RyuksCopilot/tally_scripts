from fastapi import FastAPI
from routes.createLedgerRoutes import router as ledger_router
from routes.trialBalanceRoutes import router as trial_balance_router
from routes.createVoucherRoutes import router as voucher_router
from routes.balanceSheetRoutes import router as balance_sheet_router
from routes.groupRoutes import router as group_router
from routes.inventoryRoutes import router as inventory_router

app = FastAPI()

app.include_router(group_router, prefix="/api", tags=["Group Management"])
app.include_router(ledger_router, prefix="/api", tags=["Ledger Management"])
app.include_router(trial_balance_router, prefix="/api", tags=["Trial Balance"])
app.include_router(voucher_router, prefix="/api", tags=["Voucher Management"])
app.include_router(balance_sheet_router, prefix="/api", tags=["Balance Sheet Management"])
app.include_router(inventory_router, prefix="/api", tags=["Inventory Management"])


@app.get("/")
def root():
    return {"message": "Tally API is running"}