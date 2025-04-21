from django.urls import path
from . import views

app_name = 'restaurants'

urlpatterns = [
    path('list/', views.restaurant_list, name='restaurant_list'),
    path('<slug:slug>/', views.restaurant_detail, name='restaurant_detail'),
    path('category/<int:category_id>/', views.category_food_items, name='category_food_items'),
    path('food-item/<int:item_id>/', views.food_item_detail, name='food_item_detail'),
]