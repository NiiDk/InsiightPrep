from django import forms

class CartAddPaperForm(forms.Form):
    quantity = forms.IntegerField(min_value=1, initial=1, widget=forms.HiddenInput)
    override = forms.BooleanField(required=False, initial=False, widget=forms.HiddenInput)

class CheckoutForm(forms.Form):
    email = forms.EmailField(
        label='Email Address',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'example@domain.com'})
    )
    phone_number = forms.CharField(
        label='Mobile Money Number',
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '024xxxxxxx'})
    )
