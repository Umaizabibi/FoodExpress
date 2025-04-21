from .models import Cart

def cart_processor(request):
    cart_item_count = 0
    cart_total = 0

    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            cart_item_count = cart.items.count()
            cart_total = int(cart.total_price)
        except Cart.DoesNotExist:
            cart_related_urls = ['/orders/cart/', '/orders/checkout/']
            if any(url in request.path for url in cart_related_urls):
                Cart.objects.create(user=request.user)

    return {
        'cart_item_count': cart_item_count,
        'cart_total': cart_total,
    }
