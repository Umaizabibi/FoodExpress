from django.shortcuts import render, get_object_or_404
from django.db.models import Avg, Prefetch
from .models import Restaurant, FoodCategory, FoodItem


def restaurant_list(request):
    restaurants = Restaurant.objects.filter(is_open=True)

    # Apply filters
    cuisine_type = request.GET.get('cuisine')
    if cuisine_type:
        restaurants = restaurants.filter(cuisine_type=cuisine_type)

    min_rating = request.GET.get('min_rating')
    if min_rating:
        restaurants = restaurants.filter(rating__gte=min_rating)

    # Get available cuisine types for filter dropdown
    cuisine_types = Restaurant.CUISINE_CHOICES

    context = {
        'restaurants': restaurants,
        'cuisine_types': cuisine_types,
        'selected_cuisine': cuisine_type,
        'selected_rating': min_rating,
    }

    return render(request, 'restaurants/restaurant_list.html', context)


def restaurant_detail(request, slug):
    restaurant = get_object_or_404(Restaurant, slug=slug, is_open=True)

    # Get all categories with their available food items
    # Using prefetch_related with a Prefetch object to filter food items
    categories = FoodCategory.objects.filter(restaurant=restaurant).prefetch_related(
        Prefetch(
            'food_items',
            queryset=FoodItem.objects.filter(is_available=True)
        )
    )

    context = {
        'restaurant': restaurant,
        'categories': categories,
    }

    return render(request, 'restaurants/restaurant_detail.html', context)


def category_food_items(request, category_id):
    category = get_object_or_404(FoodCategory, id=category_id)
    food_items = FoodItem.objects.filter(category=category, is_available=True)

    context = {
        'category': category,
        'food_items': food_items,
    }

    return render(request, 'restaurants/food_items_by_category.html', context)


def food_item_detail(request, item_id):
    food_item = get_object_or_404(FoodItem, id=item_id, is_available=True)

    context = {
        'food_item': food_item,
    }

    return render(request, 'restaurants/food_item_detail.html', context)