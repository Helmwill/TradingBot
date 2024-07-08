from django.urls import path
from .views import mock_create_order

urlpatterns = [
    path('orders', mock_create_order, name='mock_create_order'),
]
