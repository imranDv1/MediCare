from django.conf import settings
from django.db import models


class Sale(models.Model):
    PAYMENT_CHOICES = [
        ('waafi', 'Waafi'),
        ('evc_plus', 'Evc Plus'),
        ('cash', 'Cash'),
        ('wallet', 'Wallet'),
        ('bank', 'Bank'),
        ('card', 'Card'),
        ('debt', 'Debt'),
    ]
    invoice_no = models.CharField(max_length=50, unique=True)
    patient_name = models.CharField(max_length=200, blank=True)
    doctor_ref = models.CharField(max_length=200, blank=True, verbose_name='Doctor/Prescription Reference')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='cash')
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"Invoice #{self.invoice_no} - ${self.total}"


class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    medicine = models.ForeignKey('medicines.Medicine', on_delete=models.PROTECT)
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.medicine.name} x{self.quantity}"
