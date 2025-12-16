# shop/urls.py

from django.urls import path
from . import views

# Define the application namespace
app_name = 'shop'

urlpatterns = [
    # ====================================================================
    # 1. API ENDPOINTS (For JavaScript/AJAX calls)
    # ====================================================================
    
    # 1.1. Track downloads
    path('api/track-download/<slug:paper_slug>/', views.track_download_api, name='track_download_api'),
    
    # 1.2. Resend password
    path('api/resend-password/<str:payment_ref>/', views.resend_password_api, name='resend_password_api'),
    
    # 1.3. Check payment status
    path('payment/status/<str:reference>/', views.payment_status, name='payment_status'),
    
    # ====================================================================
    # 2. TRANSACTION / DOWNLOAD VIEWS
    # ====================================================================
    
    # 2.1. Payment initiation for paid papers
    path('buy/<slug:paper_slug>/', views.initiate_payment_or_download, name='buy_paper'),
    
    # 2.2. Direct file download (handles both free and paid papers)
    path('download/<slug:paper_slug>/', views.download_file, name='download_file'),
    
    # 2.3. Payment callback from Paystack
    path('payment/callback/', views.payment_callback, name='payment_callback'),
    
    # 2.4. Paystack webhook endpoint
    path('webhooks/paystack/', views.paystack_webhook, name='paystack_webhook'),
    
    # ====================================================================
    # 3. STATIC PAGES & UTILITY VIEWS
    # ====================================================================
    
    # 3.1. User account pages
    path('profile/', views.profile, name='profile'),
    path('history/', views.purchase_history, name='purchase_history'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('register/', views.register, name='register'),
    
    # 3.2. Contact and information pages
    path('contact/', views.contact_us, name='contact_us'),
    path('about/', views.about, name='about'),
    path('faq/', views.faq, name='faq'),
    path('privacy/', views.privacy_policy, name='privacy_policy'),
    path('terms/', views.terms_of_service, name='terms_of_service'),
    
    # ====================================================================
    # 4. SEARCH AND BROWSE VIEWS
    # ====================================================================
    
    path('search/', views.search_papers, name='search_papers'),
    path('papers/', views.all_papers, name='all_papers'),
    path('papers/year/<int:year>/', views.papers_by_year, name='papers_by_year'),
    path('papers/type/<str:exam_type>/', views.papers_by_type, name='papers_by_type'),
    
    # ====================================================================
    # 5. NAVIGATION VIEWS (Hierarchical browsing)
    # ====================================================================
    
    # 5.1. Homepage - Lists all Classes/Grades
    path('', views.class_list, name='class_list'),
    
    # 5.2. List all Terms for a Class
    path('<slug:class_slug>/', views.term_list, name='term_list'),
    
    # 5.3. List all Subjects for a Term
    path('<slug:class_slug>/<slug:term_slug>/', views.subject_list, name='subject_list'),
    
    # 5.4. List all Papers for a Subject (when there are multiple papers)
    path('<slug:class_slug>/<slug:term_slug>/<slug:subject_slug>/list/',
         views.subject_papers_list,
         name='subject_papers_list'),
    
    # 5.5. Paper Detail Page (MUST be after /list/ path)
    path('<slug:class_slug>/<slug:term_slug>/<slug:subject_slug>/<slug:paper_slug>/', 
         views.paper_detail, 
         name='paper_detail'),
]