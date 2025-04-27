from django.shortcuts import render
import yfinance as yf  

# Create your views here.
def home(request):
    stock = yf.Ticker("AAPL")
    data = stock.history(period="1mo") 
    print(data) 
    return render(request, 'home.html', {'data': data})