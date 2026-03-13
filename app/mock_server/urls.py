from django.urls import path
from .views import mock_create_order, mock_get_spot_price

urlpatterns = [
    path('orders', mock_create_order, name='mock_create_order'),
    path('spot', mock_get_spot_price, name='mock_get_spot_price'),
]
