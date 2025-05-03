from datetime import datetime, timedelta
import random
from django.core.cache import cache
from pycoingecko import CoinGeckoAPI


def generate_fake_data(symbol):
    today = datetime.today()
    dates = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(30)][::-1]
    base_price = random.uniform(10, 500)
    closes = [round(base_price + random.uniform(-5, 5) * (i / 10), 2) for i in range(30)]
    latest_price = closes[-1]

    cache.set(f"fake_price_{symbol.lower()}", latest_price, timeout=60)

    return dates, closes, latest_price

def get_coin_ids():
    coin_ids = cache.get("coin_ids")
    if coin_ids is None:
        cg = CoinGeckoAPI()
        coin_data = cg.get_coins_list()
        coin_ids = [coin['id'].lower() for coin in coin_data]
        cache.set("coin_ids", coin_ids, timeout=86400)
    return coin_ids


def is_crypto(symbol):
    return symbol.lower() in ['btc', 'bitcoin', 'eth', 'ethereum', 'xrp', 'ripple']