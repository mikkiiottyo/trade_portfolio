from django.shortcuts import render
import yfinance as yf  

# Create your views here.
def home(request):
    stock = yf.Ticker("AAPL")
    data = stock.history(period="1mo") 
    
    dates = data.index.strftime('%Y-%m-%d').tolist()
    closes = data['Close'].tolist()

    return render(request, 'home.html', {'dates': dates, 'closes': closes})