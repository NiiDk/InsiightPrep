# InsightInnovations/urls.py

from django.contrib import admin
from django.urls import path, include # 'include' is necessary for this structure
# CRITICAL FIX: Only import the specific function needed here
from shop.views import paystack_webhook 

urlpatterns = [
    # Admin path remains the same
    path('admin/', admin.site.urls),

    # 🔥 Point the root path to the shop app's URLs
    path('', include('shop.urls')),

    # The webhook MUST remain here for the Paystack link to be at the root level (e.g., /webhooks/paystack/)
    path('webhooks/paystack/', paystack_webhook, name='paystack-webhook'),
]