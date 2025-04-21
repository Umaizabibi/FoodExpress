from django.contrib import messages
from django.contrib.auth import authenticate, login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import render, redirect
from .models import Profile
from restaurants.models import Restaurant, FoodItem
from orders.models import Order

def register(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        phone = request.POST.get('phone')

        # Check if the request is AJAX
        is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

        # Validate email uniqueness
        if User.objects.filter(email=email).exists():
            error_message = 'Email is already registered.'
            if is_ajax:
                return JsonResponse({'success': False, 'error': error_message})
            messages.error(request, error_message)
            return redirect('register')

        # Validate phone uniqueness
        if Profile.objects.filter(phone=phone).exists():
            error_message = 'Phone number is already registered.'
            if is_ajax:
                return JsonResponse({'success': False, 'error': error_message})
            messages.error(request, error_message)
            return redirect('register')

        # Create user and profile
        try:
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password
            )
            Profile.objects.create(user=user, phone=phone)

            # Handle success
            if is_ajax:
                return JsonResponse({'success': True})
            messages.success(request, "Account created successfully! You can now log in.")
            return redirect('login')
        except Exception:
            error_message = "Something went wrong. Please try again."
            if is_ajax:
                return JsonResponse({'success': False, 'error': error_message})
            messages.error(request, error_message)
            return redirect('register')

    # Render the registration form for GET requests
    return render(request, 'registration.html')


def login_view(request):
    if request.method == 'POST':
        login_id = request.POST.get('login_id')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember_me')

        # Check if the request is an AJAX request
        is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

        # First try authenticating with login_id as username (email)
        user = authenticate(request, username=login_id, password=password)

        # If user not found by email, try finding by phone number
        if user is None:
            try:
                # Look up profile by phone number
                profile = Profile.objects.get(phone=login_id)
                # Then authenticate with associated user's email
                user = authenticate(request, username=profile.user.email, password=password)
            except Profile.DoesNotExist:
                user = None

        if user is not None:
            login(request, user)

            # Handle "Remember Me" functionality
            if remember_me:
                request.session.set_expiry(1209600)  # 2 weeks
            else:
                request.session.set_expiry(0)  # Session expires on browser close

            if is_ajax:
                return JsonResponse({'success': True, 'message': 'Login successful!'})
            messages.success(request, "Login successful!")
            return redirect('home')
        else:
            error_message = "Invalid email/phone or password."
            if is_ajax:
                return JsonResponse({'success': False, 'error': error_message})
            messages.error(request, error_message)
            return redirect('login')

    return render(request, 'login.html')


@login_required
def profile_view(request):
    profile = Profile.objects.get(user=request.user)

    if request.method == 'POST':
        # Determine which form was submitted based on POST data
        form_type = request.POST.get('form_type', '')

        if form_type == 'profile_update':
            # Profile update
            full_name = request.POST.get('full_name')
            phone = request.POST.get('phone')
            address = request.POST.get('address')

            # Update the User's first_name
            if full_name:
                request.user.first_name = full_name
                request.user.save()

            # Update the profile data
            profile.phone = phone
            profile.address = address
            if request.FILES.get('profile_picture'):
                profile.profile_picture = request.FILES['profile_picture']
            profile.save()

            return JsonResponse({'success': True, 'message': 'Your profile has been updated successfully!'})

        elif form_type == 'password_update':
            # Password update
            current_password = request.POST.get('current_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')

            # Validate current password
            if not request.user.check_password(current_password):
                return JsonResponse({'success': False, 'message': 'Current password is incorrect.'})

            # Validate new password and confirm password match
            if new_password != confirm_password:
                return JsonResponse({'success': False, 'message': 'New passwords do not match.'})

            # Update password
            request.user.set_password(new_password)
            request.user.save()

            # Re-authenticate user to prevent logout
            update_session_auth_hash(request, request.user)

            return JsonResponse({'success': True, 'message': 'Your password has been updated successfully!'})

    # Get recent orders for the user
    recent_orders = Order.objects.filter(user=request.user).order_by('-created_at')[:5]

    # Rendering the profile page with the current profile details and orders
    context = {
        'username': request.user.first_name,
        'email': request.user.email,
        'phone': profile.phone,
        'address': profile.address,
        'joining_date': request.user.date_joined.strftime("%d-%B-%Y"),
        'profile': profile,
        'recent_orders': recent_orders,
    }

    return render(request, 'profile.html', context)


def index(request):
    # Get top-rated restaurants (limit to 8)
    top_restaurants = Restaurant.objects.filter(is_open=True).order_by('-rating')[:8]

    # Get featured food items
    featured_items = FoodItem.objects.filter(is_featured=True, is_available=True)[:6]

    context = {
        'top_restaurants': top_restaurants,
        'featured_items': featured_items,
    }

    return render(request, 'index.html', context)


def error_404(request, exception):
    return render(request, '404.html', status=404)