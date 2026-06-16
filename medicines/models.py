from django.db import models
from django.conf import settings


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='fas fa-pills')

    class Meta:
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name


class Medicine(models.Model):
    DEFAULT_MEDICINE_IMAGE = 'https://placehold.co/400x400?text=No+Image'

    DOSAGE_FORM_CHOICES = [
        ('tablet', 'Tablet'), ('capsule', 'Capsule'), ('syrup', 'Syrup'),
        ('injection', 'Injection'), ('cream', 'Cream'), ('drops', 'Drops'),
    ]
    name = models.CharField(max_length=200)
    generic_name = models.CharField(max_length=200, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='medicines')
    brand = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    dosage_form = models.CharField(max_length=20, choices=DOSAGE_FORM_CHOICES, default='tablet')
    strength = models.CharField(max_length=100, blank=True, help_text='e.g., 500mg')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.IntegerField(default=0)
    low_stock_threshold = models.IntegerField(default=10)
    manufacturing_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField()
    supplier = models.ForeignKey('suppliers.Supplier', on_delete=models.SET_NULL, null=True, blank=True, related_name='medicines')
    image = models.URLField(max_length=500, blank=True, default='')
    barcode_sku = models.CharField(max_length=100, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.name} ({self.strength})"

    @property
    def status(self):
        if self.stock_quantity <= 0:
            return 'out_of_stock'
        elif self.stock_quantity <= self.low_stock_threshold:
            return 'low_stock'
        return 'in_stock'

    @property
    def is_expiring_soon(self):
        from datetime import date, timedelta
        if self.expiry_date:
            return self.expiry_date <= date.today() + timedelta(days=30)
        return False

    @property
    def is_expired(self):
        from datetime import date
        return self.expiry_date and self.expiry_date <= date.today()

    @property
    def stock_value(self):
        return self.price * self.stock_quantity

    @property
    def days_until_expiry(self):
        from datetime import date
        if self.expiry_date:
            return (self.expiry_date - date.today()).days
        return 0

    @property
    def image_url(self):
        return self.image or self.DEFAULT_MEDICINE_IMAGE


class StockMovement(models.Model):
    MOVEMENT_TYPES = [('IN', 'Stock In'), ('OUT', 'Stock Out')]
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, related_name='stock_movements')
    movement_type = models.CharField(max_length=3, choices=MOVEMENT_TYPES)
    quantity = models.IntegerField()
    note = models.TextField(blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.movement_type} - {self.medicine.name} x{self.quantity}"
