from django.contrib import admin
from .models import Cart, CartItem, Order, OrderItem

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ('total_price',)

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'restaurant', 'total_items', 'total_price', 'updated_at')
    search_fields = ('user__username', 'user__email', 'restaurant__name')
    readonly_fields = ('total_price', 'total_items')
    inlines = [CartItemInline]

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('total_price',)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'user', 'restaurant', 'status', 'total_amount', 'is_paid', 'created_at')
    list_filter = ('status', 'is_paid', 'payment_method', 'created_at')
    search_fields = ('order_number', 'user__username', 'user__email', 'restaurant__name')
    readonly_fields = ('order_number', 'created_at', 'updated_at', 'estimated_delivery_time')
    inlines = [OrderItemInline]
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'user', 'restaurant', 'profile', 'status')
        }),
        ('Financial Details', {
            'fields': ('total_amount', 'delivery_fee', 'tax_amount', 'payment_method', 'is_paid')
        }),
        ('Delivery Information', {
            'fields': ('delivery_address', 'delivery_instructions', 'estimated_delivery_time')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )