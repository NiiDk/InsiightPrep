# InsightInnovations/urls.py

from django.contrib import admin
from django.urls import path, include
from shop.views import paystack_webhook

# 🔥 CRITICAL IMPORTS FOR MEDIA SERVING IN DEVELOPMENT
from django.conf import settings
from django.conf.urls.static import static 

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # All base URLs ('') are now routed to the 'shop' app.
    path('', include('shop.urls')),
    
    # Paystack webhook URL must be at the root.
    path('webhooks/paystack/', paystack_webhook, name='paystack-webhook'),
]

# -------------------------------------------------------------------
# 🔥 SOLUTION FOR DOWNLOADS (Only in Development/DEBUG=True)
# -------------------------------------------------------------------
# This tells the development server to map your MEDIA_URL (/media/) 
# to your local media directory (MEDIA_ROOT), enabling file downloads.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)