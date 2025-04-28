from django.shortcuts import render
import yfinance as yf
import plotly.express as px
from plotly.io import to_html

def home(request):
    stock_symbol = request.GET.get('stock_symbol', 'AAPL')  # Default to AAPL if no symbol is provided

    stock = yf.Ticker(stock_symbol)
    data = stock.history(period="1mo")  # Get 1 month of data

    dates = data.index.strftime('%Y-%m-%d').tolist()
    closes = data['Close'].tolist()

    fig = px.line(x=dates, y=closes, labels={'x': 'Date', 'y': 'Price (USD)'}, title=f"{stock_symbol} Stock Data")
    graph_html = fig.to_html(full_html=False)



    return render(request, 'home.html', {'graph_html': graph_html, 'stock_symbol': stock_symbol})