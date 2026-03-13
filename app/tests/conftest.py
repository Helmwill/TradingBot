import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def authenticated_client(db):
    user = User.objects.create_user(username='testuser', password='testpassword')
    refresh = RefreshToken.for_user(user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION='Bearer ' + str(refresh.access_token))
    return client


@pytest.fixture
def sample_ohlcv_df():
    import pandas as pd
    import numpy as np
    np.random.seed(42)
    n = 100
    close = 175.0 + np.cumsum(np.random.randn(n) * 0.5)
    return pd.DataFrame({
        'timestamp': pd.date_range('2025-01-01', periods=n, freq='1h'),
        'open': close - 0.2,
        'high': close + 0.5,
        'low': close - 0.5,
        'close': close,
        'volume': np.abs(np.random.randn(n) * 1000) + 500,
    })
