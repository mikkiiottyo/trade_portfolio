from django.shortcuts import render
import yfinance as yf
import plotly.express as px
from pycoingecko import CoinGeckoAPI
from datetime import datetime, timezone


def home(request):
    stock_symbol = request.GET.get('stock_symbol', 'AAPL') 

    if stock_symbol.lower() == 'bitcoin':
        cg = CoinGeckoAPI()
        data = cg.get_coin_market_chart_range_by_id(id='bitcoin', vs_currency='usd', from_timestamp=1633046400, to_timestamp=1635724800)

        dates = [d[0] for d in data['prices']]  
        closes = [d[1] for d in data['prices']] 

        dates = [datetime.fromtimestamp(d / 1000, tz=timezone.utc).strftime('%Y-%m-%d') for d in dates]

    else:
        stock = yf.Ticker(stock_symbol)
        data = stock.history(period="1mo")  

       
        dates = data.index.strftime('%Y-%m-%d').tolist()
        closes = data['Close'].tolist()

  
    fig = px.line(x=dates, y=closes, labels={'x': 'Date', 'y': 'Price (USD)'}, title=f"{stock_symbol} Data")
    graph_html = fig.to_html(full_html=False)


    return render(request, 'home.html', {'graph_html': graph_html, 'stock_symbol': stock_symbol})