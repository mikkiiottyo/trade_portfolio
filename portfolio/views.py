from django.shortcuts import render
import yfinance as yf
import plotly.express as px
from plotly.io import to_html

def home(request):
    stock = yf.Ticker("AAPL")
    data = stock.history(period="1mo")

    
    fig = px.line(data, x=data.index, y="Close", title="AAPL Stock Price (Last 30 Days)")
    graph_html = to_html(fig, full_html=False)

    return render(request, 'home.html', {'graph_html': graph_html})