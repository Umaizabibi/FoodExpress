from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify


class Restaurant(models.Model):
    CUISINE_CHOICES = [
        ('ITALIAN', 'Italian'),
        ('CHINESE', 'Chinese'),
        ('MEXICAN', 'Mexican'),
        ('INDIAN', 'Indian'),
        ('AMERICAN', 'American'),
        ('JAPANESE', 'Japanese'),
        ('THAI', 'Thai'),
        ('FAST_FOOD', 'Fast Food'),
        ('OTHER', 'Other'),
    ]

    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    address = models.CharField(max_length=255)
    phone = models.CharField(max_length=15)
    email = models.EmailField()
    cuisine_type = models.CharField(max_length=20, choices=CUISINE_CHOICES, default='OTHER')
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=0.0,
                                 validators=[MinValueValidator(0.0), MaxValueValidator(5.0)])
    delivery_fee = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    minimum_order = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    estimated_delivery_time = models.IntegerField(help_text="Estimated delivery time in minutes", default=30)
    is_open = models.BooleanField(default=True)
    logo = models.ImageField(upload_to='restaurant_logos/', blank=True, null=True)
    banner_image = models.ImageField(upload_to='restaurant_banners/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class FoodCategory(models.Model):
    name = models.CharField(max_length=100)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='categories')
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name_plural = 'Food Categories'

    def __str__(self):
        return f"{self.name} ({self.restaurant.name})"


class FoodItem(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=6, decimal_places=2)
    image = models.ImageField(upload_to='food_items/', blank=True, null=True)
    category = models.ForeignKey(FoodCategory, on_delete=models.CASCADE, related_name='food_items')
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='food_items')
    is_vegetarian = models.BooleanField(default=False)
    is_vegan = models.BooleanField(default=False)
    is_gluten_free = models.BooleanField(default=False)
    spice_level = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(5)])
    is_available = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.restaurant.name})"