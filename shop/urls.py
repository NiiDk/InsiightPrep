# shop/urls.py

from django.urls import path
from . import views

app_name = 'shop'

urlpatterns = [
    # Cart
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/<int:paper_id>/', views.cart_add, name='cart_add'),
    path('cart/remove/<int:paper_id>/', views.cart_remove, name='cart_remove'),
    
    # Checkout
    path('checkout/', views.checkout, name='checkout'),
    path('order/callback/', views.order_callback, name='order_callback'),

    # Search & Browse
    path('search/', views.search_papers, name='search_papers'),
    path('papers/', views.all_papers, name='all_papers'),
    path('papers/year/<int:year>/', views.papers_by_year, name='papers_by_year'),
    path('papers/type/<str:exam_type>/', views.papers_by_type, name='papers_by_type'),
    
    # Static & Auth
    path('contact/', views.contact_us, name='contact_us'),
    path('about/', views.about, name='about'),
    path('faq/', views.faq, name='faq'),
    path('privacy/', views.privacy_policy, name='privacy_policy'),
    path('terms/', views.terms_of_service, name='terms_of_service'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    path('history/', views.purchase_history, name='purchase_history'),

    # Hierarchical Navigation (Keep at bottom)
    path('', views.class_list, name='class_list'),
    path('<slug:class_slug>/', views.term_list, name='term_list'),
    path('<slug:class_slug>/<slug:term_slug>/', views.subject_list, name='subject_list'),
    path('<slug:class_slug>/<slug:term_slug>/<slug:subject_slug>/<slug:paper_slug>/', 
         views.paper_detail, 
         name='paper_detail'),
]
