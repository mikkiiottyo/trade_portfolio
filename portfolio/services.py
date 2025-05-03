from pycoingecko import CoinGeckoAPI
import yfinance as yf
from django.core.cache import cache
from .models import UserBalance, Portfolio, Transaction
from .helpers import is_crypto,generate_fake_data, get_coin_ids
from decimal import Decimal

def get_stock_price(symbol):
    symbol = symbol.lower()
    cache_key = f"stock_price_{symbol}"
    price = cache.get(cache_key)

    if price is None:
        try:
            if is_crypto(symbol):
                cg = CoinGeckoAPI()
                crypto_ids = {
                    'btc': 'bitcoin',
                    'bitcoin': 'bitcoin',
                    'eth': 'ethereum',
                    'ethereum': 'ethereum',
                    'xrp': 'ripple',
                    'ripple': 'ripple'
                }
                coin_id = crypto_ids.get(symbol, symbol)
                crypto_data = cg.get_price(ids=coin_id, vs_currencies='usd')

                if coin_id not in crypto_data:
                    raise ValueError(f"Could not fetch price for {symbol}.")
                price = crypto_data[coin_id]['usd']
            
            else:
                stock = yf.Ticker(symbol.upper())
                hist = stock.history(period="1d")

                if hist.empty:
                    raise ValueError(f"No data returned for {symbol} from Yahoo Finance.")

                price = hist['Close'].iloc[-1]

            cache.set(cache_key, price, timeout=60)

        except Exception as e:
            print(f"Error fetching price for {symbol}: {e}")
            
            try:
                _, _, fake_price = generate_fake_data(symbol)
                price = fake_price
                cache.set(cache_key, price, timeout=60)
            except Exception as fallback_error:
                print(f"Error generating fake price for {symbol}: {fallback_error}")
                raise ValueError(f"Could not retrieve price for {symbol}. Please try again later.")
    
    return price


def handle_buy(user, symbol, shares, price):
    price = Decimal(str(price)) 
    total_cost = price * shares
    user_balance = UserBalance.objects.get(user=user)

    if user_balance.balance >= total_cost:
        user_balance.balance -= total_cost
        user_balance.save()

        portfolio_item, created = Portfolio.objects.get_or_create(
            user=user, stock_symbol=symbol,
            defaults={'shares': 0, 'average_price': 0}
        )

        if created:
            portfolio_item.shares = shares
            portfolio_item.average_price = price
        else:
            total_shares = portfolio_item.shares + shares
            portfolio_item.average_price = (
                (portfolio_item.shares * portfolio_item.average_price) + (shares * price)
            ) / total_shares
            portfolio_item.shares = total_shares

        portfolio_item.save()

        Transaction.objects.create(
            user=user,
            stock_symbol=symbol,
            shares=shares,
            price_per_share=price,
            action='BUY'
        )
        return True
    return False


def handle_sell(user, symbol, shares, price):
    try:
        price = Decimal(str(price))
        portfolio_item = Portfolio.objects.get(user=user, stock_symbol=symbol)
        if portfolio_item.shares >= shares:
            portfolio_item.shares -= shares
            user_balance = UserBalance.objects.get(user=user)
            user_balance.balance += price * shares
            user_balance.save()

            if portfolio_item.shares == 0:
                portfolio_item.delete()
            else:
                portfolio_item.save()

            Transaction.objects.create(
                user=user,
                stock_symbol=symbol,
                shares=shares,
                price_per_share=price,
                action='SELL'
            )
            return True
    except Portfolio.DoesNotExist:
        pass
    return False