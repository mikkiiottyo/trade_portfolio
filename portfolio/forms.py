from django import forms

class TradeForm(forms.Form):
    ACTION_CHOICES = [
        ('BUY', 'Buy'),
        ('SELL', 'Sell'),
    ]
    action = forms.ChoiceField(choices=ACTION_CHOICES)
    symbol = forms.CharField(label='Stock Symbol', max_length=10)
    shares = forms.DecimalField(label='Number of Shares', min_value=0.01, max_digits=10, decimal_places=2)