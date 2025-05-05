from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('trade/', views.trade_history, name='trade_history'),
]