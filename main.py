from fastapi import FastAPI
from routes.createLedgerRoutes import router as ledger_router
from routes.trialBalanceRoutes import router as trial_balance_router
from routes.createVoucherRoutes import router as voucher_router
from routes.balanceSheetRoutes import router as balance_sheet_router
from routes.groupRoutes import router as group_router
from routes.inventoryRoutes import router as inventory_router
import socket

app = FastAPI()

app.include_router(group_router, prefix="/api", tags=["Group Management"])
app.include_router(ledger_router, prefix="/api", tags=["Ledger Management"])
app.include_router(trial_balance_router, prefix="/api", tags=["Trial Balance"])
app.include_router(voucher_router, prefix="/api", tags=["Voucher Management"])
app.include_router(balance_sheet_router, prefix="/api", tags=["Balance Sheet Management"])
app.include_router(inventory_router, prefix="/api", tags=["Inventory Management"])


from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse
from pyngrok import ngrok, conf

from routes.createLedgerRoutes import router as ledger_router
from routes.trialBalanceRoutes import router as trial_balance_router
from routes.createVoucherRoutes import router as voucher_router
from routes.balanceSheetRoutes import router as balance_sheet_router
from routes.groupRoutes import router as group_router
from routes.inventoryRoutes import router as inventory_router

app = FastAPI()

# Include your routers
app.include_router(group_router, prefix="/api", tags=["Group Management"])
app.include_router(ledger_router, prefix="/api", tags=["Ledger Management"])
app.include_router(trial_balance_router, prefix="/api", tags=["Trial Balance"])
app.include_router(voucher_router, prefix="/api", tags=["Voucher Management"])
app.include_router(balance_sheet_router, prefix="/api", tags=["Balance Sheet Management"])
app.include_router(inventory_router, prefix="/api", tags=["Inventory Management"])


@app.get("/")
def root():
    return {"message": "Tally API is running"}


@app.post("/get_ngrok_url")
def get_ngrok_url(auth_token: str = Query(...)):
    """
    Open an ngrok tunnel on the given port.
    Example: POST /get_ngrok_url?auth_token=xxxx&port=8000
    """
    if not auth_token:
        raise HTTPException(status_code=400, detail="Auth token is required")

    try:
        hostname = socket.gethostname()
        # Get local IP
        local_ip = socket.gethostbyname(hostname)
        # Configure ngrok with user token
        conf.get_default().auth_token = auth_token

        # Open tunnel on given port
        public_url = ngrok.connect(8000, "http")
        
    
    
        return JSONResponse(content={"ngrok_url": str(public_url), "local_ip": local_ip})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def root():
    return {"message": "Tally API is runninng"}