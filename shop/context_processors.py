from django.utils import timezone
from .cart import Cart

def current_year(request):
    return {
        'current_year': timezone.now().year
    }

def cart(request):
    return {'cart': Cart(request)}
