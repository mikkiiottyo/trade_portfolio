from django import forms

class TradeForm(forms.Form):
    ACTION_CHOICES = [
        ('BUY', 'Buy'),
        ('SELL', 'Sell'),
        ('TRADE', 'Trade'),
    ]
    action = forms.ChoiceField(choices=ACTION_CHOICES)
    symbol = forms.CharField(label='Stock Symbol', max_length=10)
    shares = forms.DecimalField(label='Number of Shares', max_digits=10, decimal_places=2)