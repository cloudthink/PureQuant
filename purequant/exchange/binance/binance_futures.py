import hmac
import hashlib
import logging
import requests
import time
from purequant.time import get_cur_timestamp_ms
try:
    from urllib import urlencode

# for python3
except ImportError:
    from urllib.parse import urlencode


ENDPOINT = "https://www.binance.com"

BUY = "BUY"
SELL = "SELL"

LIMIT = "LIMIT"
MARKET = "MARKET"

GTC = "GTC"
IOC = "IOC"

options = {}


def set(apiKey, secret):
    """Set API key and secret.

    Must be called before any making any signed API calls.
    """
    options["apiKey"] = apiKey
    options["secret"] = secret


def depth(symbol, **kwargs):
    """Get order book.

    Args:
        symbol (str)
        limit (int, optional): Default 100. Must be one of 50, 20, 100, 500, 5,
            200, 10.

    """
    params = {"symbol": symbol}
    params.update(kwargs)
    data = request("GET", "/dapi/v1/depth", params)
    return {
        "bids": data["bids"],
        "asks": data["asks"]
    }


def klines(symbol, interval, **kwargs):
    """Get kline/candlestick bars for a symbol.

    Klines are uniquely identified by their open time. If startTime and endTime
    are not sent, the most recent klines are returned.

    Args:
        symbol (str)
        interval (str)
        limit (int, optional): Default 500; max 500.
        startTime (int, optional)
        endTime (int, optional)

    """
    params = {"symbol": symbol, "interval": interval}
    params.update(kwargs)
    data = request("GET", "/dapi/v1/klines", params)
    return data


def position():
    data = signedRequest("GET", "/dapi/v1/positionRisk", {})
    if 'msg' in data:
        raise ValueError("Error from exchange: {}".format(data['msg']))
    return data


def order(symbol, side, quantity, price, orderType=LIMIT, positionSide=None, timeInForce=GTC, test=False, **kwargs):
    positionSide = "BOTH" if positionSide is None else positionSide
    params = {
        "symbol": symbol,
        "side": side,
        "type": orderType,
        "positionSide": positionSide,
        "timeInForce": timeInForce,
        "quantity": formatNumber(quantity),
        "price": formatNumber(price)
    }
    params.update(kwargs)
    path = "/dapi/v1/order"
    data = signedRequest("POST", path, params)
    return data


def orderStatus(symbol, **kwargs):
    """Check an order's status.

    Args:
        symbol (str)
        orderId (int, optional)
        origClientOrderId (str, optional)
        recvWindow (int, optional)

    """
    params = {"symbol": symbol}
    params.update(kwargs)
    data = signedRequest("GET", "/dapi/v1/order", params)
    return data


def cancel(symbol, **kwargs):
    """Cancel an active order.

    Args:
        symbol (str)
        orderId (int, optional)
        origClientOrderId (str, optional)
        newClientOrderId (str, optional): Used to uniquely identify this
            cancel. Automatically generated by default.
        recvWindow (int, optional)

    """
    params = {"symbol": symbol}
    params.update(kwargs)
    data = signedRequest("DELETE", "/dapi/v1/order", params)
    return data


def openOrders(symbol, **kwargs):
    """Get all open orders on a symbol.

    Args:
        symbol (str)
        recvWindow (int, optional)

    """
    params = {"symbol": symbol}
    params.update(kwargs)
    data = signedRequest("GET", "/dapi/v1/openOrder", params)
    return data


def allOrders(symbol, **kwargs):
    """Get all account orders; active, canceled, or filled.

    If orderId is set, it will get orders >= that orderId. Otherwise most
    recent orders are returned.

    Args:
        symbol (str)
        orderId (int, optional)
        limit (int, optional): Default 500; max 500.
        recvWindow (int, optional)

    """
    params = {"symbol": symbol}
    params.update(kwargs)
    data = signedRequest("GET", "/dapi/v1/openOrders", params)
    return data


def myTrades(symbol, **kwargs):
    """Get trades for a specific account and symbol.

    Args:
        symbol (str)
        limit (int, optional): Default 500; max 500.
        fromId (int, optional): TradeId to fetch from. Default gets most recent
            trades.
        recvWindow (int, optional)

    """
    params = {"symbol": symbol}
    params.update(kwargs)
    data = signedRequest("GET", "/dapi/v1/userTrades", params)
    return data


def request(method, path, params=None):
    resp = requests.request(method, ENDPOINT + path, params=params)
    data = resp.json()
    if "msg" in data:
        logging.error(data['msg'])
    return data


def signedRequest(method, path, params):
    if "apiKey" not in options or "secret" not in options:
        raise ValueError("Api key and secret must be set")

    query = urlencode(sorted(params.items()))
    query += "&timestamp={}".format(get_cur_timestamp_ms() - 1000)
    secret = bytes(options["secret"].encode("utf-8"))
    signature = hmac.new(secret, query.encode("utf-8"),
                         hashlib.sha256).hexdigest()
    query += "&signature={}".format(signature)
    resp = requests.request(method,
                            ENDPOINT + path + "?" + query,
                            headers={"X-MBX-APIKEY": options["apiKey"]})
    data = resp.json()
    if "msg" in data:
        logging.error(data['msg'])
    return data


def formatNumber(x):
    if isinstance(x, float):
        return "{:.8f}".format(x)
    else:
        return str(x)

def get_ticker(symbol):
    params = {"symbol": symbol}
    data = request("GET", "/dapi/v1/ticker/price", params)
    return data


def get_contract_value(symbol):
    result = None
    params = {}
    data = request("GET", "/dapi/v1/exchangeInfo", params)
    for item in data["symbols"]:
        if item["symbol"] == symbol:
            result = int(item["contractSize"])
    return result

def set_leverage(symbol, leverage):
    """设置开仓杠杆倍数"""
    params = {"symbol": symbol,
              "leverage": leverage}
    data = signedRequest("POST", "/dapi/v1/leverage", params)
    return data