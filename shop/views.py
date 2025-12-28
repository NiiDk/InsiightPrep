# shop/views.py

import json
import requests
import logging
import re
from django import forms
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse, Http404
from django.urls import reverse
from django.db import models
from django.core.mail import send_mail
from django.db.models import Count
from django.contrib.auth.models import User
from django.contrib.auth import login as auth_login, authenticate, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Classes, Term, Subject, QuestionPaper, Payment, DownloadHistory, Order, OrderItem, Profile
from django.utils import timezone
from .cart import Cart
from .forms import CartAddPaperForm, CheckoutForm

logger = logging.getLogger(__name__)

# ====================================================================
# AUTHENTICATION FORMS
# ====================================================================

class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))
    password_confirm = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'}))
    
    class Meta:
        model = User
        fields = ['username', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}),
        }

    def clean_password_confirm(self):
        cd = self.cleaned_data
        if cd.get('password') != cd.get('password_confirm'):
            raise forms.ValidationError('Passwords do not match.')
        return cd.get('password_confirm')

class UserLoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['phone_number', 'profile_picture', 'bio']
        widgets = {
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
        }

# ====================================================================
# UTILITY FUNCTIONS
# ====================================================================

def format_ghana_phone(phone):
    if not phone: return phone
    clean_phone = re.sub(r'\D', '', str(phone))
    if clean_phone.startswith('0') and len(clean_phone) == 10:
        return f"+233{clean_phone[1:]}"
    if clean_phone.startswith('233') and len(clean_phone) == 12:
        return f"+{clean_phone}"
    if len(clean_phone) >= 9 and not str(phone).startswith('+'):
        return f"+{clean_phone}"
    return phone

def send_sms_fulfillment(phone_number, order_items):
    if not settings.HTTPSMS_API_KEY: return False
    to_phone = format_ghana_phone(phone_number)
    from_phone = "+233542232515" 
    headers = {"x-api-key": settings.HTTPSMS_API_KEY, "Content-Type": "application/json"}
    results = []
    for item in order_items:
        payload = {
            "content": f"Your password for {item.paper.title} is: {item.paper.password}. Thanks for using InsiightPrep!",
            "to": to_phone, "from": from_phone
        }
        try:
            res = requests.post("https://api.httpsms.com/v1/messages/send", headers=headers, json=payload, timeout=15)
            results.append(res.status_code in [200, 201])
        except: results.append(False)
    return all(results)

# ====================================================================
# 1. AUTHENTICATION VIEWS
# ====================================================================

def register(request):
    if request.user.is_authenticated:
        return redirect('shop:profile')
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            new_user = form.save(commit=False)
            new_user.set_password(form.cleaned_data['password'])
            new_user.save()
            Profile.objects.create(user=new_user)
            messages.success(request, 'Registration successful! You can now login.')
            return redirect('shop:login')
    else:
        form = UserRegistrationForm()
    return render(request, 'shop/register.html', {'form': form})

def login(request):
    if request.user.is_authenticated:
        return redirect('shop:profile')
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            user = authenticate(username=form.cleaned_data['username'], password=form.cleaned_data['password'])
            if user:
                auth_login(request, user)
                return redirect('shop:class_list')
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = UserLoginForm()
    return render(request, 'shop/login.html', {'form': form})

def logout(request):
    auth_logout(request)
    return redirect('shop:class_list')

@login_required
def profile(request):
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        profile = Profile.objects.create(user=request.user)
        
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('shop:profile')
    else:
        form = ProfileUpdateForm(instance=profile)
    
    # Get user's verified orders
    orders = request.user.orders.filter(verified=True).order_by('-created_at')
    return render(request, 'shop/profile.html', {'form': form, 'orders': orders, 'profile': profile})

def purchase_history(request):
    if not request.user.is_authenticated:
        return redirect('shop:login')
    return redirect('shop:profile')

# ====================================================================
# 2. CART & CHECKOUT
# ====================================================================

def cart_add(request, paper_id):
    cart = Cart(request)
    paper = get_object_or_404(QuestionPaper, id=paper_id)
    form = CartAddPaperForm(request.POST)
    if form.is_valid():
        cd = form.cleaned_data
        cart.add(paper=paper, quantity=cd['quantity'], override_quantity=cd['override'])
    return redirect('shop:cart_detail')

def cart_remove(request, paper_id):
    cart = Cart(request)
    paper = get_object_or_404(QuestionPaper, id=paper_id)
    cart.remove(paper)
    return redirect('shop:cart_detail')

def cart_detail(request):
    cart = Cart(request)
    return render(request, 'shop/cart_detail.html', {'cart': cart})

def checkout(request):
    cart = Cart(request)
    if not cart: return redirect('shop:class_list')
    
    total_price = cart.get_total_price()
    
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            order = Order.objects.create(
                user=request.user if request.user.is_authenticated else None,
                email=form.cleaned_data['email'],
                phone_number=form.cleaned_data['phone_number'],
                total_amount=total_price
            )
            for item in cart:
                OrderItem.objects.create(order=order, paper=item['paper'], price=item['price'])
            
            # Handle Free Order (Total = 0)
            if total_price == 0:
                order.verified = True
                order.save()
                send_sms_fulfillment(order.phone_number, order.items.all())
                cart.clear()
                # Use redirect() with reverse and parameters correctly
                return redirect(f"{reverse('shop:order_callback')}?reference={order.ref}")

            # Paystack API Call for Paid Orders
            url = "https://api.paystack.co/transaction/initialize"
            headers = {"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}", "Content-Type": "application/json"}
            data = {
                "email": order.email, "amount": order.amount_in_pesewas(),
                "reference": str(order.ref), "callback_url": f"{request.scheme}://{request.get_host()}{reverse('shop:order_callback')}",
                "channels": ["mobile_money"],
            }
            res = requests.post(url, headers=headers, data=json.dumps(data)).json()
            if res.get('status'):
                cart.clear()
                return redirect(res['data']['authorization_url'])
            else:
                return render(request, 'shop/error.html', {'message': 'Payment initiation failed.'})
    else:
        initial = {}
        if request.user.is_authenticated:
            try:
                initial = {'email': request.user.email, 'phone_number': request.user.profile.phone_number}
            except:
                initial = {'email': request.user.email}
        form = CheckoutForm(initial=initial)
    
    return render(request, 'shop/checkout.html', {
        'cart': cart, 
        'form': form,
        'total_price': total_price
    })

def order_callback(request):
    reference = request.GET.get('reference')
    order = get_object_or_404(Order, ref=reference)
    
    # If total price is > 0, we need to verify with Paystack
    if not order.verified and order.total_amount > 0:
        headers = {"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}", "Content-Type": "application/json"}
        res = requests.get(f"https://api.paystack.co/transaction/verify/{reference}", headers=headers).json()
        if res.get('status') and res['data']['status'] == 'success':
            order.verified = True
            order.transaction_id = res['data']['id']
            order.save()
            send_sms_fulfillment(order.phone_number, order.items.all())
    
    return render(request, 'shop/order_complete.html', {'order': order})

# ====================================================================
# 3. LIST & DETAIL VIEWS
# ====================================================================

def class_list(request):
    return render(request, 'shop/class_list.html', {
        'classes': Classes.objects.all(),
        'total_papers': QuestionPaper.objects.filter(is_available=True).count(),
        'total_downloads': DownloadHistory.objects.count(),
    })

def term_list(request, class_slug):
    class_level = get_object_or_404(Classes, slug=class_slug)
    return render(request, 'shop/term_list.html', {'class_level': class_level, 'terms': class_level.terms.all()})

def subject_list(request, class_slug, term_slug):
    class_level = get_object_or_404(Classes, slug=class_slug)
    term = get_object_or_404(Term, class_name=class_level, slug=term_slug)
    papers = QuestionPaper.objects.filter(class_level=class_level, term=term, is_available=True).select_related('subject')
    subjects = {}
    for p in papers:
        if p.subject_id not in subjects: subjects[p.subject_id] = {'subject': p.subject, 'papers': []}
        subjects[p.subject_id]['papers'].append(p)
    return render(request, 'shop/subject_list.html', {'class_level': class_level, 'term': term, 'subjects_list': list(subjects.values())})

def paper_detail(request, class_slug, term_slug, subject_slug, paper_slug):
    paper = get_object_or_404(QuestionPaper, class_level__slug=class_slug, term__slug=term_slug, subject__slug=subject_slug, slug=paper_slug, is_available=True)
    return render(request, 'shop/paper_detail.html', {'paper': paper, 'cart_paper_form': CartAddPaperForm()})

def download_file(request, paper_slug):
    paper = get_object_or_404(QuestionPaper, slug=paper_slug)
    if not paper.is_available:
        raise Http404("Not available.")
    DownloadHistory.log_download(paper=paper, request=request)
    return redirect(paper.get_secure_pdf_url())

# ====================================================================
# OTHERS
# ====================================================================
@csrf_exempt
def paystack_webhook(request):
    if request.method != 'POST': return HttpResponse(status=400)
    payload = json.loads(request.body)
    if payload.get('event') == 'charge.success':
        ref = payload['data']['reference']
        order = Order.objects.filter(ref=ref).first()
        if order and not order.verified:
            order.verified = True
            order.transaction_id = payload['data'].get('id')
            order.save()
            send_sms_fulfillment(order.phone_number, order.items.all())
    return JsonResponse({'status': 'success'})

def contact_us(request): return render(request, 'shop/contact_us.html')
def faq(request): return render(request, 'shop/faq.html')
def about(request): return render(request, 'shop/about.html')
def privacy_policy(request): return render(request, 'shop/privacy_policy.html')
def terms_of_service(request): return render(request, 'shop/terms_of_service.html')
def search_papers(request):
    q = request.GET.get('q', '').strip()
    papers = QuestionPaper.objects.filter(title__icontains=q, is_available=True) if q else []
    return render(request, 'shop/search_results.html', {'papers': papers, 'query': q})
def all_papers(request):
    return render(request, 'shop/all_papers.html', {'papers': QuestionPaper.objects.filter(is_available=True).order_by('-created_at')[:50]})
def papers_by_year(request, year): return render(request, 'shop/papers_by_year.html', {'year': year})
def papers_by_type(request, exam_type): return render(request, 'shop/papers_by_type.html', {'exam_type': exam_type})
