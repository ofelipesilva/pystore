import copy
from decimal import Decimal

from django.conf import settings

from products.models import Product
from .forms import CartAddProductForm


class Cart:
    def __init__(self, request):
        if request.session.get(settings.CART_SESSION_ID) is None:
            request.session[settings.CART_SESSION_ID] = {}

        self.cart = request.session[settings.CART_SESSION_ID]
        self.session = request.session

    def __iter__(self):
        cart = copy.deepcopy(self.cart)

        products = Product.objects.filter(id__in=cart)
        for product in products:
            cart[str(product.id)]['product'] = product

        for item in cart.values():
            item['price'] = Decimal(item['price'])
            item['total_price'] = item['price'] * item['quantity']
            item['update_quantity_form'] = CartAddProductForm(
                initial={'quantity': item['quantity'], 'override':True}
            )
            yield item

    def __len__(self):
        return sum(
            item['quantity'] for item in self.cart.values()
        )

    def add(self, product, quantity=1, override_quantity=False):
        product_id = str(product.id)
        old_quantity = 0

        if product_id in self.cart and not override_quantity:
            old_quantity = self.cart[product_id]['quantity']

        self.cart[product_id] = {
            'quantity': (quantity + old_quantity),
            'price': str(product.price)
        }

        self.cart[product_id]['quantity'] = min(20, self.cart[product_id]['quantity'])

        self.save()

    def remove(self, product):
        product_id = str(product.id)

        if product_id in self.cart:
            del self.cart[product_id]

            self.save()

    def get_total_price(self):
        return sum(
            [Decimal(item['price'])*item['quantity'] for item in self.cart.values()]
        )

    def save(self):
        self.session.modified = True