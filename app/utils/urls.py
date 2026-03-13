from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from trading.views import health_check, historical_data_view, current_prices_view, buy_request, sell_request

# S5.1 JWT Auth Audit (2026-03-13):
# All trading views (health_check, historical_data_view, current_prices_view,
# buy_request, sell_request) are decorated with @permission_classes([IsAuthenticated]).
# TokenObtainPairView and TokenRefreshView are the only unauthenticated routes — correct,
# as they are the login/token-refresh endpoints.

urlpatterns = [
    path('health/', health_check, name='health_check'),
    path('admin/', admin.site.urls),
    path('market/historical/', historical_data_view, name='historical-data'),
    path('current_prices/', current_prices_view, name='current_prices'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('buy/', buy_request, name='buy_request'),
    path('sell/', sell_request, name='sell_request'),
    path('mock/', include('mock_server.urls')),
]
