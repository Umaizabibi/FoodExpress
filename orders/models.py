from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from restaurants.models import Restaurant, FoodItem
from core.models import Profile
from django.utils import timezone
from decimal import Decimal

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart for {self.user.username}"

    @property
    def total_price(self):
        total = sum(item.total_price for item in self.items.all())
        return int(Decimal(str(total)).quantize(Decimal('1')))

    @property
    def total_items(self):
        return self.items.count()

    def clear(self):
        self.items.all().delete()
        self.restaurant = None
        self.save()


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    food_item = models.ForeignKey(FoodItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    special_instructions = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.quantity}x {self.food_item.name}"

    @property
    def total_price(self):
        from decimal import Decimal
        item_price = Decimal(str(self.food_item.price))
        quantity = Decimal(str(self.quantity))
        # Round to whole number
        return int((item_price * quantity).quantize(Decimal('1')))

    def clean(self):
        # Ensure food item is available
        if not self.food_item.is_available:
            raise ValidationError(f"Food item '{self.food_item.name}' is not available.")

        # Ensure quantity is positive
        if self.quantity <= 0:
            raise ValidationError("Quantity must be at least 1.")


class Order(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('PREPARING', 'Preparing'),
        ('OUT_FOR_DELIVERY', 'Out for delivery'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
    ]

    # Define valid status transitions
    VALID_STATUS_TRANSITIONS = {
        'PENDING': ['CONFIRMED', 'CANCELLED'],
        'CONFIRMED': ['PREPARING', 'CANCELLED'],
        'PREPARING': ['OUT_FOR_DELIVERY', 'CANCELLED'],
        'OUT_FOR_DELIVERY': ['DELIVERED', 'CANCELLED'],
        'DELIVERED': [],
        'CANCELLED': [],
    }

    PAYMENT_CHOICES = [
        ('CASH', 'Cash on Delivery'),
        ('CREDIT_CARD', 'Credit Card'),
        ('DEBIT_CARD', 'Debit Card'),
        ('MOBILE_PAYMENT', 'Mobile Payment'),
        ('ONLINE_BANKING', 'Online Banking'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='orders')
    profile = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, blank=True)
    order_number = models.CharField(max_length=20, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    total_amount = models.DecimalField(max_digits=8, decimal_places=2)
    delivery_address = models.CharField(max_length=255)
    delivery_instructions = models.TextField(blank=True, null=True)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='CASH')
    is_paid = models.BooleanField(default=False)
    delivery_fee = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    tax_amount = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    estimated_delivery_time = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        # Generate a unique order number if one doesn't exist
        if not self.order_number:
            # Generate a unique order number based on date and time
            now = timezone.now()
            self.order_number = f"FE{now.strftime('%Y%m%d%H%M%S')}{self.user.id}"

        # Set estimated delivery time if not set
        if not self.estimated_delivery_time:
            # Set estimated delivery time based on restaurant's estimated time
            self.estimated_delivery_time = timezone.now() + timezone.timedelta(
                minutes=self.restaurant.estimated_delivery_time)

        # If this is an existing order with status change, validate the transition
        if self.pk:
            old_order = Order.objects.get(pk=self.pk)
            if old_order.status != self.status:
                if self.status not in self.VALID_STATUS_TRANSITIONS.get(old_order.status, []):
                    raise ValidationError(f"Invalid status transition: {old_order.status} -> {self.status}")

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order #{self.order_number} - {self.status}"

    def can_cancel(self):
        """Check if the order can be cancelled."""
        return self.status in ['PENDING', 'CONFIRMED', 'PREPARING']

    def can_reorder(self):
        """Check if the order can be reordered."""
        return self.status in ['DELIVERED', 'CANCELLED']


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    food_item = models.ForeignKey(FoodItem, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    special_instructions = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.quantity}x {self.food_item.name} for Order #{self.order.order_number}"

    @property
    def total_price(self):
        if self.price is not None and self.quantity is not None:
            return self.price * self.quantity
        return 0

    def clean(self):
        # Ensure quantity is positive
        if self.quantity <= 0:
            raise ValidationError("Quantity must be at least 1.")