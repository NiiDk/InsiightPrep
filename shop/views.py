# shop/views.py

import json
import requests
from django import forms
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse, Http404
from django.urls import reverse
from django.db import models
from django.core.mail import send_mail
from django.db.models import Count
from .models import Classes, Term, Subject, QuestionPaper, Payment, DownloadHistory
from django.utils import timezone

# ====================================================================
# 1. HIERARCHICAL LIST VIEWS (Navigation)
# ====================================================================

def class_list(request):
    """
    Displays the top-level list of all available Classes (e.g., JHS 1).
    """
    classes = Classes.objects.all()
    
    # Get total papers count for stats
    total_papers = QuestionPaper.objects.filter(is_available=True).count()
    
    # Get download count (if available)
    total_downloads = DownloadHistory.objects.count()
    
    context = {
        'classes': classes,
        'page_title': 'Select Your Class/Grade',
        'is_homepage': True,
        'total_papers': total_papers,
        'total_downloads': total_downloads,
    }
    return render(request, 'shop/class_list.html', context)

def term_list(request, class_slug):
    """
    Displays the list of terms available for the selected Class.
    """
    class_level = get_object_or_404(Classes, slug=class_slug)
    terms = class_level.terms.all()
    
    context = {
        'class_level': class_level,
        'terms': terms,
        'page_title': f'Select Term for {class_level.name}',
    }
    return render(request, 'shop/term_list.html', context)

def subject_list(request, class_slug, term_slug):
    """
    Displays ALL subjects and ALL papers for each subject.
    """
    class_level = get_object_or_404(Classes, slug=class_slug)
    term = get_object_or_404(Term, class_name=class_level, slug=term_slug)
    
    # Get ALL available papers for this class and term
    all_papers = QuestionPaper.objects.filter(
        class_level=class_level,
        term=term,
        is_available=True
    ).select_related('subject').order_by('subject__name', '-year', 'exam_type')
    
    # Group papers by subject
    papers_by_subject = {}
    for paper in all_papers:
        if paper.subject_id not in papers_by_subject:
            papers_by_subject[paper.subject_id] = {
                'subject': paper.subject,
                'papers': []
            }
        papers_by_subject[paper.subject_id]['papers'].append(paper)
    
    # Get all subjects (including those without papers)
    all_subjects = Subject.objects.all().order_by('name')
    
    # Prepare final subjects list
    subjects_list = []
    for subject in all_subjects:
        if subject.id in papers_by_subject:
            subjects_list.append(papers_by_subject[subject.id])
        else:
            subjects_list.append({
                'subject': subject,
                'papers': []
            })
    
    context = {
        'class_level': class_level,
        'term': term,
        'subjects_list': subjects_list,
        'total_papers': all_papers.count(),
        'page_title': f'{class_level.name} {term.name} - Select Subject',
    }
    return render(request, 'shop/subject_list.html', context)

def subject_papers_list(request, class_slug, term_slug, subject_slug):
    """
    Shows ALL papers for a specific subject in a class and term.
    """
    class_level = get_object_or_404(Classes, slug=class_slug)
    term = get_object_or_404(Term, class_name=class_level, slug=term_slug)
    subject = get_object_or_404(Subject, slug=subject_slug)
    
    papers = QuestionPaper.objects.filter(
        class_level=class_level,
        term=term,
        subject=subject,
        is_available=True
    ).order_by('-year', 'exam_type', 'title')
    
    # Get related papers for sidebar/related section
    related_papers = QuestionPaper.objects.filter(
        class_level=class_level,
        term=term,
        is_available=True
    ).exclude(subject=subject).order_by('?')[:3]
    
    context = {
        'class_level': class_level,
        'term': term,
        'subject': subject,
        'papers': papers,
        'paper_count': papers.count(),
        'related_papers': related_papers,
        'page_title': f'{class_level.name} {term.name} - {subject.name} Papers',
    }
    return render(request, 'shop/paper_list.html', context)

def paper_detail(request, class_slug, term_slug, subject_slug, paper_slug):
    paper = get_object_or_404(QuestionPaper, 
        class_level__slug=class_slug,
        term__slug=term_slug,
        subject__slug=subject_slug,
        slug=paper_slug,
        is_available=True
    )
    
    # Increment view count
    paper.increment_views()
    
    # Get related papers (other papers in same subject and term)
    related_papers = QuestionPaper.objects.filter(
        class_level=paper.class_level,
        term=paper.term,
        subject=paper.subject,
        is_available=True
    ).exclude(id=paper.id).order_by('-year')[:4]
    
    # If not enough papers in same subject, get from same class
    if related_papers.count() < 2:
        additional_papers = QuestionPaper.objects.filter(
            class_level=paper.class_level,
            is_available=True
        ).exclude(id=paper.id).exclude(id__in=[p.id for p in related_papers]).order_by('?')[:4 - related_papers.count()]
        related_papers = list(related_papers) + list(additional_papers)
    
    # Determine button URL and text
    if paper.is_paid:
        button_url = reverse('shop:buy_paper', args=[paper.slug])
        button_text = "Buy Now & Get Password via SMS"
    else:
        button_url = reverse('shop:download_file', args=[paper.slug])
        button_text = "Free Download"
    
    context = {
        'paper': paper,
        'related_papers': related_papers,
        'page_title': paper.get_display_title(),
        'currency_code': settings.CURRENCY_CODE,
        'button_url': button_url,
        'button_text': button_text
    }
    return render(request, 'shop/paper_detail.html', context)

# ====================================================================
# 2. FORM DEFINITION (ADD CONTACT FORM)
# ====================================================================

class PurchaseForm(forms.Form):
    """Simple form for user input (email and phone number)"""
    email = forms.EmailField(
        label='Email Address',
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    phone_number = forms.CharField(
        label='Mobile Money Number (e.g., 024xxxxxxx)',
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

class ContactForm(forms.Form):
    """Simple form for contact enquiries."""
    name = forms.CharField(
        label='Your Name',
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., John Doe'})
    )
    email = forms.EmailField(
        label='Your Email Address',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'example@domain.com'})
    )
    subject = forms.CharField(
        label='Subject',
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enquiry about pricing'})
    )
    message = forms.Field(
        label='Your Message / Suggestion',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Please type your message here...'})
    )

# ====================================================================
# 3. MAIN CONDITIONAL LOGIC & PAYMENT INITIATION
# ====================================================================

def initiate_payment_or_download(request, paper_slug):
    """
    Handles 'shop:buy_paper'. Checks the 'is_paid' flag:
    - If False (free), redirects to the new free download landing page.
    - If True (paid), proceeds with Paystack payment initiation form.
    """
    try:
        paper = get_object_or_404(QuestionPaper, slug=paper_slug)
    except Exception:
        return render(request, 'shop/error.html', {'message': 'The requested item was not found.'})

    # === CONDITIONAL LOGIC ===
    if not paper.is_paid:
        # If the paper is FREE, redirect to download
        return redirect('shop:download_file', paper_slug=paper.slug)
    
    # === ORIGINAL PAID LOGIC (IF is_paid is checked/True) ===
    if request.method == 'POST':
        form = PurchaseForm(request.POST)

        if form.is_valid():
            email = form.cleaned_data['email']
            phone_number = form.cleaned_data['phone_number']

            # 1. Create the local Payment record (unverified)
            payment = Payment.objects.create(
                question_paper=paper,
                email=email,
                phone_number=phone_number
            )
            
            # 2. Paystack API Call Setup
            url = "https://api.paystack.co/transaction/initialize"
            headers = {
                "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
                "Content-Type": "application/json"
            }
            
            data = {
                "email": email,
                "amount": payment.amount_in_pesewas(),
                "currency": settings.CURRENCY_CODE,
                "reference": str(payment.ref),
                "callback_url": f"{request.scheme}://{request.get_host()}{reverse('shop:payment_callback')}",
                "channels": ["mobile_money"],
            }
            
            # 3. Make the request to Paystack
            response = requests.post(url, headers=headers, data=json.dumps(data))
            response_data = response.json()

            if response.status_code == 200 and response_data.get('status'):
                return redirect(response_data['data']['authorization_url'])
            else:
                print(f"Paystack Error: {response_data}") 
                return render(request, 'shop/error.html', {'message': response_data.get('message', 'Could not initiate payment.')})
    
    # Initial GET request for PAID papers: Display the form
    else:
        form = PurchaseForm()

    return render(request, 'shop/buy_paper.html', {'form': form, 'paper': paper})

# ====================================================================
# 4. FREE DOWNLOAD VIEW (UPDATED FOR CLOUDINARY)
# ====================================================================

def download_file(request, paper_slug):
    """
    Handles file downloads for both free and paid papers.
    For paid papers, requires payment verification.
    """
    paper = get_object_or_404(QuestionPaper, slug=paper_slug)
    
    # Check if paper is available
    if not paper.is_available:
        raise Http404("This paper is not available for download.")
    
    # For paid papers, check if user has paid
    if paper.is_paid:
        # Check for payment verification via session or URL parameter
        payment_ref = request.GET.get('ref')
        if not payment_ref:
            # No payment reference, redirect to purchase page
            return redirect('shop:buy_paper', paper_slug=paper.slug)
        
        # Verify payment exists and is verified
        try:
            payment = Payment.objects.get(ref=payment_ref, verified=True)
        except Payment.DoesNotExist:
            # Invalid or unverified payment
            return redirect('shop:buy_paper', paper_slug=paper.slug)
    
    # For free papers or verified paid papers, proceed with download
    if not paper.pdf_file or not paper.get_pdf_url():
        raise Http404("This paper does not have an associated file for download.")
    
    # Log download history
    user_email = request.GET.get('email', 'anonymous@example.com')
    DownloadHistory.log_download(
        paper=paper,
        email=user_email,
        request=request,
        payment=payment if paper.is_paid else None
    )
    
    # Get Cloudinary URL
    pdf_url = paper.get_secure_pdf_url()
    
    if not pdf_url:
        raise Http404("The requested paper file was not found.")
    
    # Redirect to Cloudinary URL (browser will handle download)
    return redirect(pdf_url)

# ====================================================================
# 5. PAYMENT CALLBACK VIEW (UPDATED)
# ====================================================================

def payment_callback(request):
    """
    Handles the user redirect after payment on the Paystack gateway.
    Shows success page with download options.
    """
    reference = request.GET.get('reference')
    
    if not reference:
        return redirect('shop:class_list')
    
    try:
        payment = Payment.objects.get(ref=reference)
    except Payment.DoesNotExist:
        return render(request, 'shop/error.html', {
            'message': f'Payment reference {reference} not found.',
            'page_title': 'Payment Error'
        })
    
    # Check if payment is verified
    if not payment.verified:
        # Check with Paystack
        headers = {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json"
        }
        verification_url = f"https://api.paystack.co/transaction/verify/{reference}"
        verification_response = requests.get(verification_url, headers=headers)
        
        if verification_response.status_code == 200:
            verification_data = verification_response.json()
            if (verification_data['data']['status'] == 'success' and 
                verification_data['data']['amount'] == payment.amount_in_pesewas()):
                
                # Mark as verified
                payment.mark_as_verified(
                    transaction_id=verification_data['data']['id'],
                    amount=float(verification_data['data']['amount']) / 100
                )
    
    # Create download URL with email parameter
    download_url = reverse('shop:download_file', args=[payment.question_paper.slug])
    download_url_with_params = f"{download_url}?ref={payment.ref}&email={payment.email}"
    
    context = {
        'payment': payment,
        'currency_code': settings.CURRENCY_CODE,
        'download_url': download_url_with_params,
        'page_title': 'Payment Complete'
    }
    return render(request, 'shop/callback_success.html', context)

# ====================================================================
# 6. PAYSTACK WEBHOOK HANDLER
# ====================================================================

@csrf_exempt
def paystack_webhook(request):
    """
    Handles POST requests from Paystack, verifies the payment, marks it as verified, 
    and triggers the SMS with the password.
    """
    if request.method != 'POST':
        return HttpResponse(status=400)

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponse(status=400)

    if payload.get('event') == 'charge.success':
        reference = payload['data']['reference']
        
        try:
            payment = Payment.objects.get(ref=reference)
        except Payment.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Payment reference not found'}, status=400)

        # Verify Payment with Paystack (Double Check)
        headers = {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json"
        }
        verification_url = f"https://api.paystack.co/transaction/verify/{reference}"
        verification_response = requests.get(verification_url, headers=headers)
        verification_data = verification_response.json()

        if (verification_data['data']['status'] == 'success' and 
            verification_data['data']['amount'] == payment.amount_in_pesewas()):
            
            # Mark Payment as Verified and Send Fulfillment
            if not payment.verified:
                payment.verified = True
                payment.amount_paid = float(verification_data['data']['amount']) / 100
                if verification_data['data'].get('id'):
                    payment.transaction_id = verification_data['data']['id']
                payment.save()

                question_paper = payment.question_paper
                
                # Compose the SMS message
                message = f"Your password for {question_paper.title} is: {question_paper.password}. Thank you for your purchase from Insight Innovations!" 
                
                # Arkesel API Details
                arkesel_url = "https://sms.arkesel.com/api/v2/sms/send"
                arkesel_payload = {
                    "sender": "Insight Innovations", 
                    "message": message,
                    "recipients": [payment.phone_number],
                    "apiKey": settings.ARKESEL_API_KEY
                }

                try:
                    # Send the SMS via Arkesel
                    requests.post(arkesel_url, json=arkesel_payload)
                except Exception as e:
                    # Log SMS error but don't fail the webhook
                    print(f"Error sending SMS: {e}")
                
                return JsonResponse({'status': 'success', 'message': 'Payment verified and password sent'}, status=200)
            
            return JsonResponse({'status': 'success', 'message': 'Payment already verified'}, status=200)

        return JsonResponse({'status': 'error', 'message': 'Payment verification failed'}, status=400)

    return JsonResponse({'status': 'success', 'message': 'Webhook received, but not a charge success event'}, status=200)

# ====================================================================
# 7. API VIEWS FOR TRACKING
# ====================================================================

@csrf_exempt
def track_download_api(request, paper_slug):
    """
    API endpoint to track downloads (called via JavaScript).
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        paper = get_object_or_404(QuestionPaper, slug=paper_slug)
        
        # Get data from POST request
        data = json.loads(request.body)
        email = data.get('email', 'anonymous@example.com')
        payment_ref = data.get('payment_ref')
        
        # Log download
        DownloadHistory.log_download(
            paper=paper,
            email=email,
            request=request,
            payment=Payment.objects.get(ref=payment_ref) if payment_ref else None
        )
        
        return JsonResponse({'success': True, 'message': 'Download tracked'})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def resend_password_api(request, payment_ref):
    """
    API endpoint to resend password SMS.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        payment = get_object_or_404(Payment, ref=payment_ref)
        question_paper = payment.question_paper
        
        # Compose the SMS message
        message = f"Your password for {question_paper.title} is: {question_paper.password}. Thank you for your purchase from Insight Innovations!"
        
        # Arkesel API Details
        arkesel_url = "https://sms.arkesel.com/api/v2/sms/send"
        arkesel_payload = {
            "sender": "Insight Innovations", 
            "message": message,
            "recipients": [payment.phone_number],
            "apiKey": settings.ARKESEL_API_KEY
        }
        
        response = requests.post(arkesel_url, json=arkesel_payload)
        
        if response.status_code == 200:
            return JsonResponse({'success': True, 'message': 'Password resent'})
        else:
            return JsonResponse({'error': 'Failed to send SMS'}, status=500)
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ====================================================================
# 8. ADDITIONAL VIEWS
# ====================================================================

def about(request):
    """About page"""
    context = {
        'page_title': 'About Us',
        'content': """
        <p>Welcome to <strong>Insight Innovations</strong> - your premier destination for quality educational resources.</p>
        
        <h5>Our Mission</h5>
        <p>We strive to empower students and educators by providing accessible, high-quality examination papers and learning materials.</p>
        
        <h5>What We Offer</h5>
        <ul>
            <li>Comprehensive collection of past examination papers</li>
            <li>Organized by class, term, and subject for easy navigation</li>
            <li>Both free samples and premium content</li>
            <li>Instant access after purchase</li>
            <li>Secure payment processing</li>
        </ul>
        
        <h5>Our Team</h5>
        <p>We are a team of dedicated educators and technologists passionate about improving education through technology.</p>
        """
    }
    return render(request, 'shop/about.html', context)

def faq(request):
    """Frequently Asked Questions page"""
    faqs = [
        {
            'question': 'How do I download papers?',
            'answer': 'Browse through classes, terms, and subjects to find the paper you need. Click on the paper to view details, then click "Buy Now" for paid papers or "Free Download" for free samples.'
        },
        {
            'question': 'What payment methods do you accept?',
            'answer': 'We accept Mobile Money payments through Paystack. You can pay using MTN Mobile Money, Vodafone Cash, or AirtelTigo Money.'
        },
        {
            'question': 'How do I get the password for downloaded papers?',
            'answer': 'After successful payment, the password is automatically sent to your mobile phone via SMS within minutes.'
        },
        {
            'question': 'Are the papers downloadable?',
            'answer': 'Yes! Once purchased, you can download the PDF files to your device for offline access.'
        },
        {
            'question': 'Can I get a refund?',
            'answer': 'Due to the digital nature of our products, we do not offer refunds once the paper has been downloaded. Please ensure you select the correct paper before purchasing.'
        },
        {
            'question': 'How long do I have access to purchased papers?',
            'answer': 'You have lifetime access to all papers you purchase. You can download them anytime from your purchase history.'
        },
        {
            'question': 'Do you offer bulk discounts?',
            'answer': 'Yes! Contact us directly for information about bulk purchases and institutional pricing.'
        },
    ]
    
    context = {
        'page_title': 'Frequently Asked Questions',
        'faqs': faqs
    }
    return render(request, 'shop/faq.html', context)

def privacy_policy(request):
    """Privacy policy page"""
    context = {
        'page_title': 'Privacy Policy',
        'content': """
        <h5>Information We Collect</h5>
        <p>We collect information you provide directly to us, such as when you create an account, make a purchase, or contact us for support.</p>
        
        <h5>How We Use Your Information</h5>
        <p>We use the information we collect to:</p>
        <ul>
            <li>Process your transactions and send you related information</li>
            <li>Send you technical notices and support messages</li>
            <li>Respond to your comments and questions</li>
            <li>Improve our services</li>
        </ul>
        
        <h5>Payment Information</h5>
        <p>All payments are processed through Paystack. We do not store your credit card or mobile money details on our servers.</p>
        
        <h5>Data Security</h5>
        <p>We implement reasonable security measures to protect your personal information from unauthorized access.</p>
        
        <h5>Contact Us</h5>
        <p>If you have questions about this Privacy Policy, please contact us at darkosammy2@gmail.com</p>
        """
    }
    return render(request, 'shop/privacy_policy.html', context)

def terms_of_service(request):
    """Terms of service page"""
    context = {
        'page_title': 'Terms of Service',
        'content': """
        <h5>Acceptance of Terms</h5>
        <p>By accessing and using Insight Innovations, you accept and agree to be bound by these Terms of Service.</p>
        
        <h5>Service Description</h5>
        <p>We provide digital educational resources including past examination papers. Some content is free, while other content requires payment.</p>
        
        <h5>User Accounts</h5>
        <p>You are responsible for maintaining the confidentiality of your account and password. You agree to accept responsibility for all activities that occur under your account.</p>
        
        <h5>Payments and Refunds</h5>
        <p>All payments are processed through Paystack. Due to the digital nature of our products, all sales are final and non-refundable.</p>
        
        <h5>Intellectual Property</h5>
        <p>All content on this site is protected by copyright. You may not distribute, modify, or create derivative works without our permission.</p>
        
        <h5>Limitation of Liability</h5>
        <p>Insight Innovations shall not be liable for any indirect, incidental, special, consequential, or punitive damages resulting from your use of our services.</p>
        
        <h5>Changes to Terms</h5>
        <p>We reserve the right to modify these terms at any time. Continued use of the service constitutes acceptance of the modified terms.</p>
        """
    }
    return render(request, 'shop/terms_of_service.html', context)

# ====================================================================
# 9. SEARCH AND BROWSE VIEWS
# ====================================================================

def search_papers(request):
    """Search papers across all categories"""
    query = request.GET.get('q', '').strip()
    papers = []
    
    if query:
        papers = QuestionPaper.objects.filter(
            models.Q(title__icontains=query) |
            models.Q(subject__name__icontains=query) |
            models.Q(class_level__name__icontains=query) |
            models.Q(description__icontains=query),
            is_available=True
        ).select_related('class_level', 'term', 'subject').order_by('-created_at')[:50]
    
    context = {
        'query': query,
        'papers': papers,
        'results_count': len(papers),
        'page_title': f'Search Results for "{query}"' if query else 'Search Papers'
    }
    return render(request, 'shop/search_results.html', context)

def all_papers(request):
    """Display all papers across all categories"""
    papers = QuestionPaper.objects.filter(
        is_available=True
    ).select_related('class_level', 'term', 'subject').order_by('-created_at')[:100]
    
    context = {
        'papers': papers,
        'page_title': 'All Question Papers',
        'total_count': papers.count()
    }
    return render(request, 'shop/all_papers.html', context)

# ====================================================================
# 10. CONTACT VIEW
# ====================================================================

def contact_us(request):
    """
    Handles the contact form display and submission, and sends the message via email.
    """
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            visitor_email = form.cleaned_data['email']
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']
            
            # 1. Compose the Email Content
            full_subject = f"[CONTACT FORM] {subject} - From: {name}"
            email_body = f"Message received from the website contact form.\n\n"
            email_body += f"Name: {name}\n"
            email_body += f"Email: {visitor_email}\n"
            email_body += f"Subject: {subject}\n\n"
            email_body += f"--- MESSAGE CONTENT ---\n{message}\n---------------------\n"
            
            try:
                # 2. Send Email to the Admin (Your Account)
                send_mail(
                    full_subject,
                    email_body,
                    settings.DEFAULT_FROM_EMAIL,
                    ['darkosammy2@gmail.com'],
                    fail_silently=False,
                )
                
                # Optional: Send Confirmation to the Visitor (Good practice)
                send_mail(
                    f"Confirmation: We received your message",
                    f"Dear {name},\n\nThank you for reaching out to us. We have received your message regarding: '{subject}'. We will respond as soon as possible.\n\n---\nInsight Innovations Team",
                    settings.DEFAULT_FROM_EMAIL,
                    [visitor_email],
                    fail_silently=True,
                )
                
                context = {
                    'page_title': 'Message Sent',
                    'success': True,
                    'name': name
                }
                return render(request, 'shop/contact_us.html', context)

            except Exception as e:
                # Handle email sending errors (e.g., incorrect settings)
                print(f"Error sending contact email: {e}")
                context = {
                    'page_title': 'Contact Us - Error',
                    'form': form,
                    'success': False,
                    'email_error': 'There was a server error sending your message. Please try again or call us.',
                    'phone': '+233542232515', 
                    'email': 'darkosammy2@gmail.com',
                    'location': 'Accra, Ghana'
                }
                return render(request, 'shop/contact_us.html', context)
    
    # Initial GET request or non-valid form submission
    else:
        form = ContactForm()
    
    context = {
        'page_title': 'Contact Us',
        'form': form,
        'success': False,
        'phone': '+233542232515', 
        'email': 'darkosammy2@gmail.com',
        'location': 'Accra, Ghana'
    }
    
    return render(request, 'shop/contact_us.html', context)

# ====================================================================
# 11. UTILITY VIEWS
# ====================================================================

def profile(request):
    """Placeholder for My Profile view."""
    return render(request, 'shop/profile.html', {'page_title': 'My Profile'})

def purchase_history(request):
    """Placeholder for Purchase History view."""
    return render(request, 'shop/purchase_history.html', {'page_title': 'Purchase History'})

def login(request):
    """Placeholder for Login view."""
    return redirect('admin:login')

def logout(request):
    """Placeholder for Logout view."""
    return redirect('shop:class_list')

def register(request):
    """Placeholder for Register view."""
    return render(request, 'shop/register.html', {'page_title': 'Register'})

def payment_status(request, reference):
    """Check payment status"""
    try:
        payment = Payment.objects.get(ref=reference)
        context = {
            'payment': payment,
            'page_title': 'Payment Status'
        }
        return render(request, 'shop/payment_status.html', context)
    except Payment.DoesNotExist:
        return render(request, 'shop/error.html', {
            'message': f'Payment reference {reference} not found.',
            'page_title': 'Payment Not Found'
        })
def your_view(request):
    context = {
        'current_year': timezone.now().year,
        # ... other context
    }
    return render(request, 'template.html', context)

def papers_by_year(request, year):
    """
    Display all available papers for a specific year.
    """
    papers = QuestionPaper.objects.filter(
        year=year,
        is_available=True
    ).select_related('class_level', 'term', 'subject').order_by(
        'class_level__name',
        'term__name',
        'subject__name'
    )

    if not papers.exists():
        raise Http404("No papers found for this year.")

    context = {
        'papers': papers,
        'year': year,
        'total_count': papers.count(),
        'page_title': f'Question Papers for {year}'
    }
    return render(request, 'shop/papers_by_year.html', context)
def papers_by_type(request, exam_type):
    """
    Display papers filtered by exam type (e.g. BECE, Mock, End of Term).
    """
    papers = QuestionPaper.objects.filter(
        exam_type__iexact=exam_type,
        is_available=True
    ).select_related('class_level', 'term', 'subject').order_by(
        '-year',
        'class_level__name'
    )

    if not papers.exists():
        raise Http404("No papers found for this exam type.")

    context = {
        'papers': papers,
        'exam_type': exam_type,
        'total_count': papers.count(),
        'page_title': f'{exam_type} Question Papers'
    }
    return render(request, 'shop/papers_by_type.html', context)
