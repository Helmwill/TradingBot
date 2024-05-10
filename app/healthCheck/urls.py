from django.contrib import admin
from django.urls import path
from healthstatus.views import health_check  # Adjust app name as necessary

urlpatterns = [
    path('health/', health_check, name='health_check'),
    path('admin/', admin.site.urls),
]
