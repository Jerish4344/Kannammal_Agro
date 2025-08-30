"""Order models for procurement management."""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator

from core.models import BaseModel


class Order(BaseModel):
    """Orders placed with farmers for procurement."""
    
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('confirmed', _('Confirmed')),
        ('in_progress', _('In Progress')),
        ('ready', _('Ready for Pickup')),
        ('picked_up', _('Picked Up')),
        ('delivered', _('Delivered')),
        ('cancelled', _('Cancelled')),
        ('rejected', _('Rejected')),
    ]
    
    order_number = models.CharField(
        max_length=20,
        unique=True,
        verbose_name=_('Order Number')
    )
    sku = models.ForeignKey(
        'catalog.SKU',
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name=_('SKU')
    )
    farmer = models.ForeignKey(
        'farmers.Farmer',
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name=_('Farmer')
    )
    region = models.ForeignKey(
        'regions.Region',
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name=_('Region')
    )
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        verbose_name=_('Quantity Ordered')
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        verbose_name=_('Unit Price')
    )
    total_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        verbose_name=_('Total Amount')
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name=_('Status')
    )
    ordered_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='placed_orders',
        verbose_name=_('Ordered By')
    )
    approved_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_orders',
        verbose_name=_('Approved By')
    )
    assigned_buyer = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_orders',
        verbose_name=_('Assigned Buyer')
    )
    expected_delivery_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Expected Delivery Date')
    )
    actual_delivery_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Actual Delivery Date')
    )
    delivered_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name=_('Delivered Quantity')
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_('Order Notes')
    )
    farmer_notes = models.TextField(
        blank=True,
        verbose_name=_('Farmer Notes')
    )
    
    class Meta:
        verbose_name = _('Order')
        verbose_name_plural = _('Orders')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['farmer', 'status']),
            models.Index(fields=['region', 'status']),
        ]
        
    def __str__(self):
        return f"{self.order_number} - {self.farmer} - {self.sku.name}"
    
    def save(self, *args, **kwargs):
        """Auto-calculate total amount and generate order number."""
        if not self.order_number:
            from django.utils import timezone
            timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
            self.order_number = f"ORD{timestamp}"
        
        self.total_amount = self.quantity * self.unit_price
        super().save(*args, **kwargs)
    
    @property
    def is_on_time(self):
        """Check if order was delivered on time."""
        if not self.actual_delivery_date or not self.expected_delivery_date:
            return None
        return self.actual_delivery_date <= self.expected_delivery_date
    
    @property
    def fill_rate(self):
        """Calculate order fill rate (delivered quantity / ordered quantity)."""
        if not self.delivered_quantity:
            return 0
        return (self.delivered_quantity / self.quantity) * 100
    
    @property
    def days_to_delivery(self):
        """Calculate days between order and delivery."""
        if not self.actual_delivery_date:
            return None
        return (self.actual_delivery_date - self.created_at.date()).days
    
    def can_be_cancelled(self):
        """Check if order can be cancelled."""
        return self.status in ['pending', 'confirmed']
    
    def can_be_confirmed(self):
        """Check if order can be confirmed."""
        return self.status == 'pending'


class OrderStatusHistory(models.Model):
    """Track order status changes."""
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='status_history',
        verbose_name=_('Order')
    )
    old_status = models.CharField(
        max_length=20,
        verbose_name=_('Old Status')
    )
    new_status = models.CharField(
        max_length=20,
        verbose_name=_('New Status')
    )
    changed_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='order_status_changes',
        verbose_name=_('Changed By')
    )
    changed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Changed At')
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_('Change Notes')
    )
    
    class Meta:
        verbose_name = _('Order Status History')
        verbose_name_plural = _('Order Status Histories')
        ordering = ['-changed_at']
        
    def __str__(self):
        return f"{self.order.order_number}: {self.old_status} → {self.new_status}"


class OrderPayment(BaseModel):
    """Payment records for orders."""
    
    PAYMENT_METHODS = [
        ('cash', _('Cash')),
        ('bank_transfer', _('Bank Transfer')),
        ('upi', _('UPI')),
        ('cheque', _('Cheque')),
    ]
    
    PAYMENT_STATUS = [
        ('pending', _('Pending')),
        ('processing', _('Processing')),
        ('completed', _('Completed')),
        ('failed', _('Failed')),
        ('refunded', _('Refunded')),
    ]
    
    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name='payment',
        verbose_name=_('Order')
    )
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        verbose_name=_('Payment Amount')
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHODS,
        verbose_name=_('Payment Method')
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS,
        default='pending',
        verbose_name=_('Payment Status')
    )
    transaction_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Transaction ID')
    )
    payment_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Payment Date')
    )
    processed_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processed_payments',
        verbose_name=_('Processed By')
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_('Payment Notes')
    )
    
    class Meta:
        verbose_name = _('Order Payment')
        verbose_name_plural = _('Order Payments')
        
    def __str__(self):
        return f"Payment for {self.order.order_number} - ₹{self.amount}"
