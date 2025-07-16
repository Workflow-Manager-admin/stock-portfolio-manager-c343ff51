import os
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from dotenv import load_dotenv
import httpx

# Import Kite Connect service wrapper
from .kite_service import (
    get_request_token_url,
    generate_access_token,
    place_order_kite,
    get_profile,
    KiteAuthError
)

# Load .env variables
load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

KITE_API_KEY = os.environ.get("KITE_API_KEY") or os.environ.get("ZERODHA_KITE_API_KEY")
KITE_API_SECRET = os.environ.get("KITE_API_SECRET") or os.environ.get("ZERODHA_KITE_API_SECRET")

app = FastAPI(
    title="Stock Portfolio Manager API",
    description="REST API for stock portfolio management: authentication, portfolio, P&L, trading, recommendations, analytics.",
    version="1.0.0",
    openapi_tags=[
        {"name": "auth", "description": "Authentication and registration."},
        {"name": "portfolio", "description": "Portfolio listing and stock positions."},
        {"name": "pnl", "description": "Profit and Loss calculations."},
        {"name": "recommendations", "description": "Investment and options recommendations."},
        {"name": "order", "description": "Order placement via Zerodha Kite."},
        {"name": "analytics", "description": "Portfolio analytics and visualization."},
    ],
)

# CORS handling, allow all origins (for demo)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# =======================
# === Data Models =======
# =======================

class UserRegisterModel(BaseModel):
    email: str = Field(..., description="Email address")
    password: str = Field(..., min_length=6, description="Password")


class UserLoginModel(BaseModel):
    email: str = Field(..., description="Email address")
    password: str = Field(..., description="Password")


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class PortfolioItem(BaseModel):
    symbol: str
    quantity: float
    avg_price: float
    current_price: float
    invested_value: float
    current_value: float
    profit_loss: float


class PortfolioOut(BaseModel):
    holdings: List[PortfolioItem]
    cash: float


class PnlItem(BaseModel):
    symbol: str
    realized: float
    unrealized: float


class PnlOut(BaseModel):
    pnl: List[PnlItem]


class Recommendation(BaseModel):
    symbol: str
    reason: str
    type: str  # e.g. "BUY", "SELL", "OPTION", etc.


class OrderRequest(BaseModel):
    symbol: str = Field(..., description="Stock symbol")
    quantity: float = Field(..., description="Order quantity")
    transaction_type: str = Field(..., description="BUY or SELL")
    order_type: str = Field(..., description="Order type (e.g., MARKET, LIMIT)")
    price: Optional[float] = Field(None, description="Limit price, if applicable")


class OrderResponse(BaseModel):
    status: str
    order_id: Optional[str]
    message: Optional[str]


class AnalyticsRequest(BaseModel):
    # e.g. filter by date range, portfolio subset, etc. For now, empty.
    pass


class AnalyticsResponse(BaseModel):
    # Just a structure for demo. Real implementation can have detailed analytics.
    total_invested: float
    total_current: float
    total_return: float
    return_percent: float
    asset_allocation: Dict[str, float]  # e.g. sector -> percent


# ===========================
# === HELPER FUNCTIONS ======
# ===========================

async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """
    Validate Supabase JWT, return user info. Raise on failure.
    """
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    url = f"{SUPABASE_URL}/auth/v1/user"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {token}"
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers)
        if resp.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid token")
        return resp.json()

# ===========================
# === ROUTES/API ============ 
# ===========================

@app.get("/")
def health_check():
    """Health check endpoint."""
    return {"message": "Healthy"}

# PUBLIC_INTERFACE
@app.post("/auth/register", summary="User Registration", tags=["auth"], response_model=TokenOut)
async def register(user: UserRegisterModel):
    """
    Register a new user in Supabase.

    - **email**: Email address
    - **password**: Password (minimum 6 chars)
    """
    url = f"{SUPABASE_URL}/auth/v1/signup"
    data = {"email": user.email, "password": user.password}
    headers = {
        "apikey": SUPABASE_KEY,
        "Content-Type": "application/json"
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=data, headers=headers)
        if resp.status_code != 200:
            raise HTTPException(status_code=400, detail=resp.json())
        token = resp.json().get("access_token", "")
        return TokenOut(access_token=token)


# PUBLIC_INTERFACE
@app.post("/auth/login", summary="User Login", tags=["auth"], response_model=TokenOut)
async def login(user: UserLoginModel):
    """
    User login using Supabase.

    - **email**: Email address
    - **password**: Password
    Returns JWT token on success.
    """
    url = f"{SUPABASE_URL}/auth/v1/token?grant_type=password"
    data = {"email": user.email, "password": user.password}
    headers = {
        "apikey": SUPABASE_KEY,
        "Content-Type": "application/json"
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=data, headers=headers)
        if resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Login failed")
        token = resp.json().get("access_token", "")
        return TokenOut(access_token=token)


# PUBLIC_INTERFACE
@app.get("/portfolio", summary="Get user portfolio", response_model=PortfolioOut, tags=["portfolio"])
async def get_portfolio(user: dict = Depends(get_current_user)):
    """
    Fetch the user's stock portfolio (dummy example; should connect to DB/broker in production).

    Returns list of holdings and cash.
    """
    # Simulated data - replace with DB/broker logic
    holdings = [
        PortfolioItem(
            symbol="AAPL",
            quantity=10,
            avg_price=150,
            current_price=170,
            invested_value=1500,
            current_value=1700,
            profit_loss=200,
        ),
        PortfolioItem(
            symbol="TSLA",
            quantity=5,
            avg_price=500,
            current_price=700,
            invested_value=2500,
            current_value=3500,
            profit_loss=1000,
        ),
    ]
    cash = 3000.0
    return PortfolioOut(holdings=holdings, cash=cash)


# PUBLIC_INTERFACE
@app.get("/pnl", summary="Profit and Loss details", response_model=PnlOut, tags=["pnl"])
async def get_pnl(user: dict = Depends(get_current_user)):
    """
    Return realized and unrealized profit/loss for user's positions.
    """
    pnl = [
        PnlItem(symbol="AAPL", realized=120, unrealized=80),
        PnlItem(symbol="TSLA", realized=400, unrealized=600),
    ]
    return PnlOut(pnl=pnl)


# PUBLIC_INTERFACE
@app.get("/recommendations", summary="Get stock/investment recommendations", response_model=List[Recommendation], tags=["recommendations"])
async def get_recommendations(user: dict = Depends(get_current_user)):
    """
    Return a list of recommendations for investments and options trading.
    """
    return [
        Recommendation(symbol="MSFT", reason="Strong earnings, solid growth", type="BUY"),
        Recommendation(symbol="NIFTY21SEP30000CE", reason="Bullish trend, short-term momentum", type="OPTION"),
    ]

# PUBLIC_INTERFACE
@app.get("/kite/oauth-url", tags=["order"], summary="Get Zerodha Kite OAuth URL")
async def kite_oauth_url():
    """
    Get the Zerodha Kite OAuth authentication/authorization URL.
    Redirect users to this URL to login and approve access.
    """
    url = await get_request_token_url()
    return {"kite_auth_url": url}

# PUBLIC_INTERFACE
@app.post("/kite/generate-token", tags=["order"], summary="Generate Zerodha Kite Access Token")
async def kite_generate_token(request_token: str = Query(..., description="Request token from Zerodha OAuth redirect")):
    """
    Obtain Zerodha Kite access_token (user must authenticate via OAuth first).
    Input: `request_token` (from OAuth callback)
    Returns: dict containing access_token, public_token, etc.
    """
    try:
        token_data = await generate_access_token(request_token)
        return token_data
    except KiteAuthError as ex:
        raise HTTPException(status_code=400, detail=str(ex))

# PUBLIC_INTERFACE
@app.post("/order", summary="Place order via Zerodha Kite", response_model=OrderResponse, tags=["order"])
async def place_order(
    order: OrderRequest,
    access_token: str = Query(..., description="User's Zerodha Kite access_token (from /kite/generate-token)"),
    user: dict = Depends(get_current_user)
):
    """
    Place an order via Zerodha Kite API.

    - **symbol**: Stock symbol
    - **quantity**: Amount to buy/sell
    - **transaction_type**: BUY or SELL
    - **order_type**: MARKET, LIMIT, etc.
    - **price**: Limit price, if order_type is LIMIT

    Requires user's Zerodha Kite `access_token`.
    """
    try:
        result = await place_order_kite(access_token, order.model_dump())
        return OrderResponse(
            status="success",
            order_id=result.get("order_id", ""),
            message="Order placed successfully via Zerodha Kite."
        )
    except KiteAuthError as ex:
        return OrderResponse(status="failed", order_id=None, message=str(ex))
    except Exception as ex:
        return OrderResponse(status="failed", order_id=None, message=str(ex))

# PUBLIC_INTERFACE
@app.get("/kite/profile", tags=["order"], summary="Get Kite Connect User Profile")
async def kite_profile(
    access_token: str = Query(..., description="User's Zerodha Kite access_token (from /kite/generate-token)"),
    user: dict = Depends(get_current_user)
):
    """
    Fetch the authenticated user's Zerodha profile using the access token.
    """
    try:
        profile = await get_profile(access_token)
        return profile
    except KiteAuthError as ex:
        raise HTTPException(status_code=400, detail=str(ex))

# PUBLIC_INTERFACE
@app.get("/analytics", summary="View portfolio analytics", response_model=AnalyticsResponse, tags=["analytics"])
async def get_analytics(user: dict = Depends(get_current_user)):
    """
    Provide analytics on user's portfolio (returns, allocation, etc.).
    """
    return AnalyticsResponse(
        total_invested=4000,
        total_current=5200,
        total_return=1200,
        return_percent=30.0,
        asset_allocation={
            "Tech": 60.0,
            "EV": 30.0,
            "Cash": 10.0,
        }
    )

# PUBLIC_INTERFACE
@app.get("/ws-info", summary="WebSocket API Info", tags=["analytics"])
def api_ws_usage():
    """
    For real-time features, WebSocket endpoints could be documented here.
    """
    return {
        "websocket_url": "wss://.../ws",
        "note": "WebSocket API not implemented yet. For real-time P&L or analytics, subscribe here (future)."
    }

# === End of main.py ===
