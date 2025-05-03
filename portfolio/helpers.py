from datetime import datetime, timedelta
import random
from django.core.cache import cache
from pycoingecko import CoinGeckoAPI


def generate_fake_data(stock_symbol):
    dates = [(datetime.today() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(30)]
    closes = [random.uniform(100, 200) for _ in range(30)]
    return dates, closes


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