from django.shortcuts import render, redirect
import yfinance as yf
import plotly.express as px
import random
from datetime import datetime, timezone, timedelta  
import time
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




def generate_fake_data(stock_symbol):
    dates = [datetime.today().strftime('%Y-%m-%d')] 
    for i in range(1, 30):
        dates.append((datetime.today() - timedelta(days=i)).strftime('%Y-%m-%d'))

    closes = [random.uniform(100, 200) for _ in range(30)] 

    return dates, closes

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

    return render(request, 'home.html', {'graph_html': graph_html, 'stock_symbol': stock_symbol, 'error_message': error_message if 'error_message' in locals() else None})