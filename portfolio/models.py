from django.db import models
from django.contrib.auth.models import User

class Portfolio(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    stock_symbol = models.CharField(max_length=10)
    shares = models.DecimalField(max_digits=10, decimal_places=2)
    average_price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ('user', 'stock_symbol')

    def __str__(self):
        return f"{self.user.username} owns {self.shares} shares of {self.stock_symbol}"

class UserBalance(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=10000.00)

    def __str__(self):
        return f"{self.user.username} - Balance: ${self.balance}"

class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    stock_symbol = models.CharField(max_length=10)
    shares = models.DecimalField(max_digits=10, decimal_places=2)
    price_per_share = models.DecimalField(max_digits=10, decimal_places=2)
    action = models.CharField(max_length=5, choices=[('BUY', 'Buy'), ('SELL', 'Sell'), ('TRADE', 'Trade')])
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} {self.action} {self.shares} of {self.stock_symbol} at ${self.price_per_share} each"