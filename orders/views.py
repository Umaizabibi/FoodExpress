from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction, OperationalError
from django.utils import timezone
from time import sleep
from decimal import Decimal
from .models import Cart, CartItem, Order, OrderItem
from restaurants.models import Restaurant, FoodItem
from core.models import Profile


@login_required
def cart_view(request):
    try:
        cart = Cart.objects.get(user=request.user)
        cart_items = cart.items.all().select_related('food_item')
    except Cart.DoesNotExist:
        cart = Cart.objects.create(user=request.user)
        cart_items = []

    context = {
        'cart': cart,
        'cart_items': cart_items,
    }

    return render(request, 'orders/cart.html', context)


@login_required
@transaction.atomic
def add_to_cart(request):
    if request.method == 'POST':
        food_item_id = request.POST.get('food_item_id')
        quantity = int(request.POST.get('quantity', 1))
        special_instructions = request.POST.get('special_instructions', '')

        try:
            # Get the food item
            food_item = get_object_or_404(FoodItem, id=food_item_id, is_available=True)

            # Get or create cart
            cart, created = Cart.objects.get_or_create(user=request.user)

            # Check if adding from a different restaurant
            if cart.restaurant and cart.restaurant != food_item.restaurant:
                # Ask user if they want to clear the cart and start a new order
                if request.POST.get('confirm_clear') != 'true':
                    return JsonResponse({
                        'status': 'restaurant_mismatch',
                        'message': f'Your cart contains items from {cart.restaurant.name}. Would you like to clear your cart and add this item from {food_item.restaurant.name}?'
                    })
                else:
                    # User confirmed, clear the cart
                    cart.items.all().delete()

            # Set the restaurant if cart is empty
            if not cart.restaurant:
                cart.restaurant = food_item.restaurant
                cart.save()

            # Check if item already exists in cart
            existing_items = CartItem.objects.filter(cart=cart, food_item=food_item)

            if existing_items.exists():
                # Get the first existing item
                cart_item = existing_items.first()

                # Update quantity
                cart_item.quantity = quantity

                # Update special instructions if provided
                if special_instructions:
                    cart_item.special_instructions = special_instructions

                cart_item.save()
                message = f"Updated quantity for {food_item.name} in your cart."
            else:
                # Create new cart item
                cart_item = CartItem.objects.create(
                    cart=cart,
                    food_item=food_item,
                    quantity=quantity,
                    special_instructions=special_instructions
                )
                message = f"Added {food_item.name} to your cart."

            return JsonResponse({
                'status': 'success',
                'message': message,
                'cart_total': float(cart.total_price),
                'cart_count': cart.items.count(),
            })

        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Error: {str(e)}',
            }, status=500)

    return JsonResponse({'status': 'error', 'message': 'Invalid request'})


@login_required
def update_cart_item(request, cart_item_id):
    cart_item = get_object_or_404(CartItem, id=cart_item_id, cart__user=request.user)

    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))

        if quantity <= 0:
            # Remove item if quantity is 0 or negative
            cart_item.delete()
            messages.success(request, f"Removed {cart_item.food_item.name} from your cart.")
        else:
            # Update quantity
            cart_item.quantity = quantity
            special_instructions = request.POST.get('special_instructions')
            if special_instructions is not None:
                cart_item.special_instructions = special_instructions
            cart_item.save()
            messages.success(request, f"Updated {cart_item.food_item.name} quantity.")

        # Check if this was an AJAX request
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            cart = cart_item.cart
            return JsonResponse({
                'status': 'success',
                'cart_total': float(cart.total_price),
                'item_total': float(cart_item.total_price) if quantity > 0 else 0,
                'cart_count': cart.items.count(),
            })

    return redirect('orders:cart_view')


@login_required
def remove_from_cart(request, cart_item_id):
    cart_item = get_object_or_404(CartItem, id=cart_item_id, cart__user=request.user)
    food_item_name = cart_item.food_item.name
    cart_item.delete()

    messages.success(request, f"Removed {food_item_name} from your cart.")

    # Check if this was an AJAX request
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        cart = Cart.objects.get(user=request.user)
        return JsonResponse({
            'status': 'success',
            'cart_total': float(cart.total_price),
            'cart_count': cart.items.count(),
        })

    return redirect('orders:cart_view')


@login_required
def clear_cart(request):
    try:
        cart = Cart.objects.get(user=request.user)
        cart.clear()
        messages.success(request, "Your cart has been cleared.")
    except Cart.DoesNotExist:
        pass

    # Check if this was an AJAX request
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success',
            'message': 'Cart cleared successfully.'
        })

    return redirect('orders:cart_view')


@login_required
def checkout(request):
    try:
        cart = Cart.objects.get(user=request.user)
        if cart.items.count() == 0:
            messages.warning(request, "Your cart is empty. Add some items before checkout.")
            return redirect('restaurants:restaurant_list')

        profile = Profile.objects.get(user=request.user)

        # Calculate totals as whole numbers, without tax
        subtotal = cart.total_price
        delivery_fee = int(cart.restaurant.delivery_fee)
        grand_total = subtotal + delivery_fee

        context = {
            'cart': cart,
            'cart_items': cart.items.all(),
            'profile': profile,
            'subtotal': subtotal,
            'delivery_fee': delivery_fee,
            'grand_total': grand_total,
        }

        return render(request, 'orders/checkout.html', context)

    except Cart.DoesNotExist:
        messages.warning(request, "Your cart is empty. Add some items before checkout.")
        return redirect('restaurants:restaurant_list')
    except Profile.DoesNotExist:
        messages.error(request, "Your profile is incomplete. Please update your profile first.")
        return redirect('profile')


@login_required
@transaction.atomic
def place_order(request):
    if request.method != 'POST':
        return redirect('orders:checkout')

    try:
        cart = Cart.objects.get(user=request.user)
        if cart.items.count() == 0:
            messages.warning(request, "Your cart is empty.")
            return redirect('restaurants:restaurant_list')

        profile = Profile.objects.get(user=request.user)

        # Get form data
        delivery_address = request.POST.get('delivery_address', profile.address)
        delivery_instructions = request.POST.get('delivery_instructions', '')
        payment_method = request.POST.get('payment_method', 'CASH')

        # Calculate totals as whole numbers, without tax
        subtotal = cart.total_price
        delivery_fee = int(cart.restaurant.delivery_fee)
        grand_total = subtotal + delivery_fee

        # Create order
        order = Order.objects.create(
            user=request.user,
            restaurant=cart.restaurant,
            profile=profile,
            total_amount=grand_total,
            delivery_address=delivery_address,
            delivery_instructions=delivery_instructions,
            payment_method=payment_method,
            delivery_fee=delivery_fee,
            tax_amount=0,
        )

        # Create order items
        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                food_item=cart_item.food_item,
                quantity=cart_item.quantity,
                price=cart_item.food_item.price,
                special_instructions=cart_item.special_instructions,
            )

        # Empty the cart
        cart.clear()

        messages.success(request, f"Your order (#{order.order_number}) has been placed successfully!")
        return redirect('orders:order_confirmation', order_number=order.order_number)

    except Cart.DoesNotExist:
        messages.warning(request, "Your cart is empty.")
        return redirect('restaurants:restaurant_list')
    except Profile.DoesNotExist:
        messages.error(request, "Your profile is incomplete. Please update your profile.")
        return redirect('profile')
    except Exception as e:
        messages.error(request, f"Error processing your order: {str(e)}")
        return redirect('orders:checkout')

@login_required
def order_confirmation(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)

    context = {
        'order': order,
        'order_items': order.items.all(),
    }

    return render(request, 'orders/order_confirmation.html', context)


@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')

    context = {
        'orders': orders,
    }

    return render(request, 'orders/order_history.html', context)


@login_required
def order_detail(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)

    context = {
        'order': order,
        'order_items': order.items.all(),
    }

    return render(request, 'orders/order_detail.html', context)


@login_required
def cancel_order(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)

    if not order.can_cancel():
        messages.error(request, "This order cannot be canceled.")
        return redirect('orders:order_detail', order_number=order_number)

    if request.method == 'POST':
        # Update order status to CANCELLED
        order.status = 'CANCELLED'
        order.save()

        messages.success(request, f"Order #{order_number} has been cancelled successfully.")
        return redirect('orders:order_history')

    # Show confirmation page for GET requests
    context = {
        'order': order,
    }

    return render(request, 'orders/cancel_order.html', context)