from django.shortcuts import render, redirect
import yfinance as yf
import plotly.express as px
import random
from datetime import datetime, timezone, timedelta
import time
from django.core.cache import cache
from pycoingecko import CoinGeckoAPI
from django.contrib.auth.forms import UserCreationForm
from .forms import TradeForm
from django.contrib.auth import login
from .models import UserBalance, Portfolio, Transaction
from django.contrib.auth.decorators import login_required


def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user) 
            UserBalance.objects.create(user=user, balance=10000.00)

            return redirect('home') 
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})

@login_required
def home(request):
    stock_symbol = request.GET.get('stock_symbol', 'AAPL').strip().lower() 

    cg = CoinGeckoAPI()

    if stock_symbol not in ['aapl', 'msft', 'goog']:  
        try:
            if stock_symbol:  
                coin_data = cg.get_coins_list()  
                coin_ids = [coin['id'].lower() for coin in coin_data] 

                if stock_symbol in coin_ids:  
                    current_timestamp = int(time.time())
                    one_year_ago_timestamp = current_timestamp - (365 * 24 * 60 * 60)  
                    
                    data = cg.get_coin_market_chart_range_by_id(
                        id=stock_symbol, vs_currency='usd', from_timestamp=one_year_ago_timestamp, to_timestamp=current_timestamp
                    )
                    
                    dates = [d[0] for d in data['prices']]  
                    closes = [d[1] for d in data['prices']] 

                    dates = [datetime.fromtimestamp(d / 1000, tz=timezone.utc).strftime('%Y-%m-%d') for d in dates]
                    stock_symbol = stock_symbol.capitalize() 
                else:
                    dates, closes = generate_fake_data(stock_symbol)
                    stock_symbol = stock_symbol.capitalize()  
            else:
                raise ValueError("Please enter a valid cryptocurrency or stock ticker.")
        except Exception as e:
            error_message = str(e)
            dates, closes, stock_symbol = [], [], "Invalid Search"
    else:
        try:
            stock = yf.Ticker(stock_symbol.upper()) 
            data = stock.history(period="1mo")

            if data.empty:
                raise ValueError(f"Invalid stock symbol: {stock_symbol}")
            
            dates = data.index.strftime('%Y-%m-%d').tolist()  
            closes = data['Close'].tolist()  
            stock_symbol = stock_symbol.upper()  
        except Exception as e:
            error_message = str(e)
            dates, closes, stock_symbol = [], [], "Invalid Search"

    if not dates or not closes:
        error_message = "No data available for the given symbol."
        return render(request, 'home.html', {'error_message': error_message})

    fig = px.line(x=dates, y=closes, labels={'x': 'Date', 'y': 'Price (USD)'}, title=f"{stock_symbol} Data")
    graph_html = fig.to_html(full_html=False)

    user_balance = None
    if request.user.is_authenticated:
        try:
            user_balance = UserBalance.objects.get(user=request.user).balance
        except UserBalance.DoesNotExist:
            user_balance = 0

    if request.method == 'POST':
        action = request.POST.get('action')
        symbol = request.POST.get('symbol').upper()
        shares = int(request.POST.get('shares'))
        price = get_stock_price(symbol)  

        if action == 'BUY':
            handle_buy(request, symbol, shares, price)
        elif action == 'SELL':
            handle_sell(request, symbol, shares, price)

        return redirect('home')  

    return render(request, 'home.html', {
        'graph_html': graph_html,
        'stock_symbol': stock_symbol,
        'error_message': error_message if 'error_message' in locals() else None,
        'user_balance': user_balance,
    })

@login_required
def trade_history(request):
    transactions = Transaction.objects.filter(user=request.user).order_by('-id')
    return render(request, 'trade.html', {
        'transactions': transactions
    })

def handle_buy(request, symbol, shares, price):
    total_cost = price * shares
    user_balance = UserBalance.objects.get(user=request.user)
    
    if user_balance.balance >= total_cost:
        user_balance.balance -= total_cost
        user_balance.save()
        portfolio_item, created = Portfolio.objects.get_or_create(
            user=request.user, stock_symbol=symbol,
            defaults={'shares': 0, 'average_price': 0}
        )
        if created:
            portfolio_item.shares = shares
            portfolio_item.average_price = price
        else:
            total_shares = portfolio_item.shares + shares
            portfolio_item.average_price = ((portfolio_item.shares * portfolio_item.average_price) + (shares * price)) / total_shares
            portfolio_item.shares = total_shares

        portfolio_item.save()
        Transaction.objects.create(
            user=request.user,
            stock_symbol=symbol,
            shares=shares,
            price_per_share=price,
            action='BUY'
        )
    else:
        return render(request, 'home.html', {'error': 'Not enough balance to buy.'})

def handle_sell(request, symbol, shares, price):
    try:
        portfolio_item = Portfolio.objects.get(user=request.user, stock_symbol=symbol)
        if portfolio_item.shares >= shares:
            portfolio_item.shares -= shares
            user_balance = UserBalance.objects.get(user=request.user)
            user_balance.balance += price * shares
            user_balance.save()

            if portfolio_item.shares == 0:
                portfolio_item.delete()
            else:
                portfolio_item.save()
            Transaction.objects.create(
                user=request.user,
                stock_symbol=symbol,
                shares=shares,
                price_per_share=price,
                action='SELL'
            )
        else:
            return render(request, 'home.html', {'error': 'Not enough shares to sell.'})
    except Portfolio.DoesNotExist:
        return render(request, 'home.html', {'error': 'You do not own this stock.'})

def get_stock_price(symbol):
    symbol = symbol.lower()
    cache_key = f"stock_price_{symbol}"
    price = cache.get(cache_key)

    if price is None:
        try:
            if symbol in ['bitcoin', 'btc', 'ethereum', 'eth', 'ripple', 'xrp']:
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
                price = crypto_data[coin_id]['usd']
            else:
                stock = yf.Ticker(symbol.upper())
                hist = stock.history(period="1d")
                if hist.empty:
                    raise Exception("No data returned from yfinance.")
                price = hist['Close'].iloc[-1]
            
            cache.set(cache_key, price, timeout=60)
        except Exception as e:
            print(f"Error fetching price for {symbol}: {e}")
            raise Exception("Could not retrieve stock price. Try again soon.")

    return price

def generate_fake_data(stock_symbol):
    dates = [datetime.today().strftime('%Y-%m-%d')] 
    for i in range(1, 30):
        dates.append((datetime.today() - timedelta(days=i)).strftime('%Y-%m-%d'))

    closes = [random.uniform(100, 200) for _ in range(30)] 

    return dates, closes