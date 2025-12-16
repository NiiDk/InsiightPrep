# core/forms.py

from django import forms
from .models import Payment

class PurchaseForm(forms.ModelForm):
    # We only need the customer's contact info for the payment
    class Meta:
        model = Payment
        fields = ['email', 'phone_number']