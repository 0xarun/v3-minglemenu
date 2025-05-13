from django.db import models, transaction
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid
from django.db.models import F, Max
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.utils import timezone

class Store(models.Model):
    store_id = models.CharField(max_length=50, unique=True)
    store_name = models.CharField(max_length=100)
    edited_text = models.TextField()
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    menu_items = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ['-id']  # This will order stores by id in descending order
        verbose_name = "Store"
        verbose_name_plural = "Stores"
        
    @classmethod
    def get_next_store_number(cls):
        with transaction.atomic():
            try:
                # Get all store_ids
                store_ids = cls.objects.values_list('store_id', flat=True)
                # Extract numbers from store_ids
                numbers = [int(sid.split('-')[1]) for sid in store_ids if sid.startswith('store-') and sid.split('-')[1].isdigit()]
                max_num = max(numbers) if numbers else 0
            except ObjectDoesNotExist:
                max_num = 0

            next_num = max_num + 1
            while cls.objects.filter(store_id=f'store-{next_num}').exists():
                next_num += 1

            return next_num

    @classmethod
    def generate_store_id(cls):
        return f'store-{cls.get_next_store_number()}'

class BusinessOwner(models.Model):
    store = models.OneToOneField(Store, on_delete=models.CASCADE, null=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    upi_id = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"{self.store.store_name} - {self.first_name} {self.last_name}"

def generate_cart_id():
    return str(uuid.uuid4())

class CartItem(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, null=True)
    item_name = models.CharField(max_length=55)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    quantity = models.PositiveIntegerField(default=1)
    cart_id = models.CharField(max_length=50, default=generate_cart_id)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)


    def __str__(self):
        return f"{self.store.store_id} - {self.item_name} - {self.quantity}"

    def total_price(self):
        return self.price * self.quantity

class Order(models.Model):
    ORDER_TYPE_CHOICES = [
        ('dine_in', 'Dine-In'),
        ('takeaway', 'Takeaway'),
        ('delivery', 'Home Delivery'),
    ]
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Pay on Shop'),
        ('upi', 'UPI'),
    ]
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    store_order_id = models.PositiveIntegerField(null=True, blank=True)  # Allow null temporarily
    items = models.ManyToManyField(CartItem, related_name='orders')
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    customer_name = models.CharField(max_length=100, null=True)
    customer_phone = models.CharField(max_length=15, null=True)
    order_type = models.CharField(max_length=20, choices=ORDER_TYPE_CHOICES, null=True)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('EXPIRED', 'Expired')
    ], default='PENDING')

    class Meta:
        unique_together = ['store', 'store_order_id']

    def save(self, *args, **kwargs):
        if self.store_order_id is None:
            last_order = Order.objects.filter(store=self.store).exclude(store_order_id=None).order_by('-store_order_id').first()
            self.store_order_id = (last_order.store_order_id + 1) if last_order else 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.store.store_name} - Order {self.store_order_id}"

    #def __str__(self):
     #   return f"Order {self.id} - {self.customer_name} - {self.get_order_type_display()}"  # Fixed: added closing parenthesis

class Payment(models.Model):
    payment_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    upi_id = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=[
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('EXPIRED', 'Expired')
    ], default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment {self.id} for {self.store.store_name} - {self.status}"


class Offer(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='offers')
    title = models.CharField(max_length=100)
    description = models.TextField()
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.store.store_name} - {self.title}"

class Advertisement(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='advertisements')
    title = models.CharField(max_length=100)
    content = models.TextField()
    image = models.ImageField(upload_to='advertisements/', blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.store.store_name} - {self.title}"

class CouponCode(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='coupons')
    code = models.CharField(max_length=20, unique=True)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    is_active = models.BooleanField(default=True)
    expiry_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.store.store_name} - {self.code}"

    def is_valid(self):
        return self.is_active and self.expiry_date > timezone.now()