from django.contrib import admin
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from trading.views import (
    health_check,
    historical_data_view,
    current_prices_view,
    buy_request,
    sell_request,
    bot_status,
    bot_trades,
    api_containers,
    api_stats,
)

urlpatterns = [
    path('health/', health_check, name='health_check'),
    path('admin/', admin.site.urls),
    path('market/historical/', historical_data_view, name='historical-data'),
    path('current_prices/', current_prices_view, name='current_prices'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/containers/', api_containers, name='api-containers'),
    path('api/stats/', api_stats, name='api-stats'),
    path('buy/', buy_request, name='buy_request'),
    path('sell/', sell_request, name='sell_request'),
    path('bot/status/', bot_status, name='bot_status'),
    path('bot/trades/', bot_trades, name='bot_trades'),
]
