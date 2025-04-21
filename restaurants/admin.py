from django.contrib import admin
from .models import Restaurant, FoodCategory, FoodItem

class FoodCategoryInline(admin.TabularInline):
    model = FoodCategory
    extra = 1

class FoodItemInline(admin.TabularInline):
    model = FoodItem
    extra = 1
    fields = ('name', 'price', 'category', 'is_available', 'is_featured')

@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ('name', 'cuisine_type', 'rating', 'is_open', 'created_at')
    list_filter = ('cuisine_type', 'is_open')
    search_fields = ('name', 'description', 'address')
    readonly_fields = ('created_at', 'updated_at')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [FoodCategoryInline]

@admin.register(FoodCategory)
class FoodCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'restaurant', 'order')
    list_filter = ('restaurant',)
    search_fields = ('name', 'restaurant__name')
    inlines = [FoodItemInline]

@admin.register(FoodItem)
class FoodItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'restaurant', 'price', 'is_available', 'is_featured')
    list_filter = ('is_available', 'is_featured', 'is_vegetarian', 'restaurant', 'category')
    search_fields = ('name', 'description', 'restaurant__name', 'category__name')
    list_editable = ('price', 'is_available', 'is_featured')