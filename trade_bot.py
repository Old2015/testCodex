import os
import time
import hmac
import hashlib
import urllib.request
import urllib.parse
import json

BASE_URL = "https://fapi.binance.com"

API_KEY = os.getenv("BINANCE_API_KEY", "")
API_SECRET = os.getenv("BINANCE_API_SECRET", "")


def send_signed_request(method, path, params=None):
    if params is None:
        params = {}
    params['timestamp'] = int(time.time() * 1000)
    query_string = urllib.parse.urlencode(params)
    signature = hmac.new(API_SECRET.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
    url = f"{BASE_URL}{path}?{query_string}&signature={signature}"
    req = urllib.request.Request(url, method=method)
    req.add_header("X-MBX-APIKEY", API_KEY)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def send_public_request(method, path, params=None):
    if params:
        query_string = urllib.parse.urlencode(params)
        url = f"{BASE_URL}{path}?{query_string}"
    else:
        url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url, method=method)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def get_market_price(symbol):
    data = send_public_request("GET", "/fapi/v1/ticker/price", {"symbol": symbol})
    return float(data['price'])


def fetch_economic_sentiment():
    url = "https://api.coindesk.com/v1/bpi/currentprice.json"
    try:
        with urllib.request.urlopen(url) as resp:
            data = json.loads(resp.read())
        # very naive sentiment example
        usd_rate = float(data['bpi']['USD']['rate'].replace(',', ''))
        if usd_rate > 0:
            return "positive"
        return "neutral"
    except Exception:
        return "neutral"


def analyze(price, sentiment):
    if sentiment == "positive":
        return "BUY"
    elif sentiment == "negative":
        return "SELL"
    else:
        return None


def place_market_order(symbol, side, quantity):
    params = {
        "symbol": symbol,
        "side": side,
        "type": "MARKET",
        "quantity": quantity,
    }
    return send_signed_request("POST", "/fapi/v1/order", params)


def place_stop_order(symbol, side, stop_price, order_type):
    params = {
        "symbol": symbol,
        "side": side,
        "type": order_type,
        "stopPrice": stop_price,
        "closePosition": True,
        "workingType": "CONTRACT_PRICE",
    }
    return send_signed_request("POST", "/fapi/v1/order", params)


def wait_for_order(symbol, order_id, timeout=60):
    end_time = time.time() + timeout
    while time.time() < end_time:
        params = {"symbol": symbol, "orderId": order_id}
        data = send_signed_request("GET", "/fapi/v1/order", params)
        if data.get("status") in ("FILLED", "CANCELED", "REJECTED", "EXPIRED"):
            return data.get("status")
        time.sleep(1)
    return "UNKNOWN"


def main():
    symbol = "BTCUSDT"
    quantity = 0.001
    price = get_market_price(symbol)
    sentiment = fetch_economic_sentiment()
    side = analyze(price, sentiment)
    if not side:
        print("No clear signal. Skipping trade.")
        return
    stop = price * (0.99 if side == "BUY" else 1.01)
    take = price * (1.01 if side == "BUY" else 0.99)

    order = place_market_order(symbol, side, quantity)
    order_id = order.get("orderId")
    if not order_id:
        print("Order failed:", order)
        return

    opposite = "SELL" if side == "BUY" else "BUY"
    place_stop_order(symbol, opposite, stop, "STOP_MARKET")
    place_stop_order(symbol, opposite, take, "TAKE_PROFIT_MARKET")

    status = wait_for_order(symbol, order_id)
    print("Final order status:", status)


if __name__ == "__main__":
    main()
