import pytest
import numpy as np
import pandas as pd
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
    """100-bar OHLCV fixture — enough bars for RSI+MACD computation."""
    rng = np.random.default_rng(seed=42)
    n = 100
    close = 175.0 + rng.standard_normal(n).cumsum() * 0.5
    return pd.DataFrame({
        'timestamp': pd.date_range('2025-01-01', periods=n, freq='5min'),
        'open': close - rng.uniform(0, 0.2, n),
        'high': close + rng.uniform(0, 0.5, n),
        'low': close - rng.uniform(0, 0.5, n),
        'close': close,
        'volume': rng.uniform(1000, 10000, n),
    })


@pytest.fixture
def backtest_fixture_df():
    """200-bar OHLCV fixture for backtest Sharpe/drawdown CI gate."""
    rng = np.random.default_rng(seed=99)
    n = 200
    close = 175.0 + rng.standard_normal(n).cumsum() * 0.4
    return pd.DataFrame({
        'timestamp': pd.date_range('2025-06-01', periods=n, freq='1h'),
        'open': close - rng.uniform(0, 0.2, n),
        'high': close + rng.uniform(0, 0.5, n),
        'low': close - rng.uniform(0, 0.5, n),
        'close': close,
        'volume': rng.uniform(500, 5000, n),
    })

