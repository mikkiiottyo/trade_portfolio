from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from .forms import TradeForm
from .models import UserBalance, Portfolio, Transaction
from .helpers import generate_fake_data, get_coin_ids, is_crypto
from .services import get_stock_price, handle_buy, handle_sell
from pycoingecko import CoinGeckoAPI
import yfinance as yf
import plotly.express as px
from datetime import datetime, timezone, timedelta
import time
from decimal import Decimal

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
  
    stock_symbol = request.GET.get('stock_symbol', 'AAPL').strip()
    
    if not isinstance(stock_symbol, str):
        stock_symbol = 'AAPL'  

    if not stock_symbol.isalpha():
        stock_symbol = 'AAPL'  

    error_message = None
    dates, closes = [], []

    valid_stocks = ['aapl', 'msft', 'goog']
    if stock_symbol.lower() not in valid_stocks:
        try:
            coin_ids = get_coin_ids()
            if stock_symbol.lower() in coin_ids:
                current_timestamp = int(time.time())
                one_year_ago_timestamp = current_timestamp - (365 * 24 * 60 * 60)

                cg = CoinGeckoAPI()
                data = cg.get_coin_market_chart_range_by_id(
                    id=stock_symbol.lower(), vs_currency='usd',
                    from_timestamp=one_year_ago_timestamp, to_timestamp=current_timestamp
                )

                dates = [datetime.fromtimestamp(d[0] / 1000, tz=timezone.utc).strftime('%Y-%m-%d') for d in data['prices']]
                closes = [d[1] for d in data['prices']]
                stock_symbol = stock_symbol.capitalize()
            else:  
                dates, closes, stock_symbol = generate_fake_data(stock_symbol)
                stock_symbol = stock_symbol.capitalize()
        except Exception as e:
            error_message = str(e)
            dates, closes, stock_symbol = generate_fake_data(stock_symbol)
            stock_symbol = stock_symbol.capitalize()
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
            dates, closes, stock_symbol = generate_fake_data(stock_symbol)
            stock_symbol = stock_symbol.capitalize()

    if not dates or not closes:
        return render(request, 'home.html', {
            'error_message': "No data available for the given symbol."
        })

    fig = px.line(x=dates, y=closes, labels={'x': 'Date', 'y': 'Price (USD)'}, title=f"{stock_symbol} Data")
    graph_html = fig.to_html(full_html=False)

    user_balance = 0
    try:
        user_balance = UserBalance.objects.get(user=request.user).balance
    except UserBalance.DoesNotExist:
        pass

    portfolio = Portfolio.objects.filter(user=request.user)

    portfolio_data = []
    for item in portfolio:
        try:
            current_price = Decimal(str(get_stock_price(item.stock_symbol)))
            total_value = item.shares * current_price
            total_cost = item.shares * item.average_price
            gain_loss = total_value - total_cost
            gain_loss_percent = (gain_loss / total_cost * 100) if total_cost > 0 else 0

            portfolio_data.append({
                'symbol': item.stock_symbol,
                'shares': item.shares,
                'avg_price': item.average_price,
                'current_price': round(current_price, 2),
                'total_value': round(total_value, 2),
                'gain_loss': round(gain_loss, 2),
                'gain_loss_percent': round(gain_loss_percent, 2)
            })
        except ValueError as e:
            print(f"Error fetching price for {item.stock_symbol}: {e}")
            portfolio_data.append({
                'symbol': item.stock_symbol,
                'error': str(e)
            })

    if request.method == 'POST':
        action = request.POST.get('action')
        symbol = request.POST.get('symbol').upper()
        shares = int(request.POST.get('shares'))
        try:
            price = get_stock_price(symbol)
        except ValueError as e:
            error_message = str(e)
            return render(request, 'home.html', {
                'graph_html': graph_html,
                'stock_symbol': stock_symbol,
                'error_message': error_message,
                'user_balance': user_balance,
                'portfolio_data': portfolio_data,
            })

        success = False
        if action == 'BUY':
            success = handle_buy(request.user, symbol, shares, price)
        elif action == 'SELL':
            success = handle_sell(request.user, symbol, shares, price)

        if not success:
            error_message = "Transaction failed. Check your balance or available shares."
            return render(request, 'home.html', {
                'graph_html': graph_html,
                'stock_symbol': stock_symbol,
                'error_message': error_message,
                'user_balance': user_balance,
                'portfolio_data': portfolio_data,
            })

    return render(request, 'home.html', {
        'graph_html': graph_html,
        'stock_symbol': stock_symbol,
        'error_message': error_message,
        'user_balance': user_balance,
        'portfolio_data': portfolio_data,
    })


@login_required
def trade_history(request):
    transactions = Transaction.objects.filter(user=request.user).order_by('-id')
    return render(request, 'trade.html', {
        'transactions': transactions
    })
