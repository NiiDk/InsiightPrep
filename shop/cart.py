from decimal import Decimal
from django.conf import settings
from .models import QuestionPaper

class Cart:
    def __init__(self, request):
        """Initialize the cart."""
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            # save an empty cart in the session
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart

    def add(self, paper, quantity=1, override_quantity=False):
        """Add a paper to the cart or update its quantity."""
        paper_id = str(paper.id)
        if paper_id not in self.cart:
            self.cart[paper_id] = {'quantity': 0, 'price': str(paper.price)}
        
        if override_quantity:
            self.cart[paper_id]['quantity'] = quantity
        else:
            self.cart[paper_id]['quantity'] += quantity
        self.save()

    def save(self):
        # mark the session as "modified" to make sure it gets saved
        self.session.modified = True

    def remove(self, paper):
        """Remove a paper from the cart."""
        paper_id = str(paper.id)
        if paper_id in self.cart:
            del self.cart[paper_id]
            self.save()

    def __iter__(self):
        """Iterate over the items in the cart and get the papers from the database."""
        paper_ids = self.cart.keys()
        # get the paper objects and add them to the cart
        papers = QuestionPaper.objects.filter(id__in=paper_ids)
        cart = self.cart.copy()
        for paper in papers:
            cart[str(paper.id)]['paper'] = paper

        for item in cart.values():
            item['price'] = Decimal(item['price'])
            item['total_price'] = item['price'] * item['quantity']
            yield item

    def __len__(self):
        """Count all items in the cart."""
        return sum(item['quantity'] for item in self.cart.values())

    def get_total_price(self):
        return sum(Decimal(item['price']) * item['quantity'] for item in self.cart.values())

    def clear(self):
        # remove cart from session
        del self.session[settings.CART_SESSION_ID]
        self.save()
