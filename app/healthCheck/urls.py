from django.contrib import admin
from django.urls import path
from healthstatus.views import health_check, coinbase_historical_data_view, current_prices_view

urlpatterns = [
    path('health/', health_check, name='health_check'),
    path('admin/', admin.site.urls),
    path('coinbase/historical/', coinbase_historical_data_view, name='coinbase-historical-data'),
    path('current_prices/', current_prices_view, name='current_prices'),
]


