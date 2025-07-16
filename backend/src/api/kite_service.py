import os
from dotenv import load_dotenv
import httpx
from typing import Dict

load_dotenv()

KITE_API_KEY = os.environ.get("KITE_API_KEY") or os.environ.get("ZERODHA_KITE_API_KEY")
KITE_API_SECRET = os.environ.get("KITE_API_SECRET") or os.environ.get("ZERODHA_KITE_API_SECRET")
KITE_BASE_URL = "https://api.kite.trade"

class KiteAuthError(Exception):
    pass

# PUBLIC_INTERFACE
async def get_request_token_url():
    """
    Returns the URL where users should be redirected to login with Zerodha and approve access.
    Used for obtaining the request_token in OAuth flow.
    """
    return f"https://kite.trade/connect/login?api_key={KITE_API_KEY}&v=3"

# PUBLIC_INTERFACE
async def generate_access_token(request_token: str) -> Dict:
    """
    Exchange request_token for access_token.
    :param request_token: The request token obtained from the redirect URL.
    :return: dict containing access_token, public_token, etc.
    Raises KiteAuthError on failure.
    """
    url = f"{KITE_BASE_URL}/session/token"
    headers = {
        "X-Kite-Version": "3",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "api_key": KITE_API_KEY,
        "request_token": request_token,
        "api_secret": KITE_API_SECRET
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, data=data, headers=headers)
        if resp.status_code != 200:
            raise KiteAuthError(f"Failed to obtain access token: {resp.text}")
        token_data = resp.json()
        if "data" not in token_data:
            raise KiteAuthError(f"Invalid token response: {token_data}")
        return token_data["data"]

# PUBLIC_INTERFACE
async def place_order_kite(access_token: str, order_details: Dict) -> Dict:
    """
    Places an order with Zerodha Kite Connect API.
    :param access_token: User-specific access token.
    :param order_details: Dict containing symbol, quantity, transaction_type, order_type, price.
    :return: dict API response (order_id, status, etc).
    Raises KiteAuthError on failure.
    """
    url = f"{KITE_BASE_URL}/orders/regular"
    headers = {
        "X-Kite-Version": "3",
        "Authorization": f"token {KITE_API_KEY}:{access_token}"
    }
    payload = {
        "tradingsymbol": order_details["symbol"],
        "exchange": order_details.get("exchange", "NSE"),
        "transaction_type": order_details["transaction_type"],
        "order_type": order_details["order_type"],
        "quantity": int(order_details["quantity"]),
        "product": order_details.get("product", "CNC"),
    }
    price = order_details.get("price")
    if payload["order_type"].upper() == "LIMIT" and price is not None:
        payload["price"] = float(price)
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, data=payload, headers=headers)
        if resp.status_code not in (200, 201):
            raise KiteAuthError(f"Order failed: {resp.text}")
        return resp.json().get("data", {})

# PUBLIC_INTERFACE
async def get_profile(access_token: str) -> Dict:
    """
    Fetches the user profile from Kite Connect.
    :param access_token: User's access token.
    :return: dict with profile details.
    """
    url = f"{KITE_BASE_URL}/user/profile"
    headers = {
        "X-Kite-Version": "3",
        "Authorization": f"token {KITE_API_KEY}:{access_token}"
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers)
        if resp.status_code != 200:
            raise KiteAuthError("Failed to fetch profile")
        return resp.json().get("data", {})
