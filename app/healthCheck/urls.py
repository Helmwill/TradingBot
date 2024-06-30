from django.contrib import admin
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView,TokenRefreshView
from healthstatus.views import health_check, coinbase_historical_data_view, current_prices_view, buy_request, sell_request

urlpatterns = [
    path('health/', health_check, name='health_check'),
    path('admin/', admin.site.urls),
    path('coinbase/historical/', coinbase_historical_data_view, name='coinbase-historical-data'),
    path('current_prices/', current_prices_view, name='current_prices'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('buy/', buy_request, name='buy_request'),
    path('sell/', sell_request, name='sell_request'),
]


