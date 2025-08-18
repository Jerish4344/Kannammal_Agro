"""Farmer models for Kannammal Agro."""

from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models import BaseModel


class Farmer(BaseModel):
    """Farmer profile and information."""
    
    user = models.OneToOneField(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='farmer_profile',
        verbose_name=_('User Account')
    )
    region = models.ForeignKey(
        'regions.Region',
        on_delete=models.CASCADE,
        related_name='farmers',
        verbose_name=_('Region')
    )
    farmer_id = models.CharField(
        max_length=20,
        unique=True,
        verbose_name=_('Farmer ID')
    )
    contact_number = models.CharField(
        max_length=15,
        verbose_name=_('Contact Number')
    )
    alternate_contact = models.CharField(
        max_length=15,
        blank=True,
        verbose_name=_('Alternate Contact')
    )
    address = models.TextField(
        verbose_name=_('Address')
    )
    farm_size = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Farm Size (acres)')
    )
    farm_type = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Farm Type')
    )
    bank_account_number = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('Bank Account Number')
    )
    bank_ifsc = models.CharField(
        max_length=11,
        blank=True,
        verbose_name=_('Bank IFSC Code')
    )
    bank_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Bank Name')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Is Active')
    )
    verified_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Verified At')
    )
    verified_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_farmers',
        verbose_name=_('Verified By')
    )
    
    class Meta:
        verbose_name = _('Farmer')
        verbose_name_plural = _('Farmers')
        ordering = ['farmer_id']
        
    def __str__(self):
        return f"{self.farmer_id} - {self.user.get_full_name() or self.user.username}"
    
    @property
    def is_verified(self):
        """Check if farmer is verified."""
        return self.verified_at is not None
    
    @property
    def total_orders_count(self):
        """Get total number of orders for this farmer."""
        return self.orders.filter(deleted_at__isnull=True).count()
    
    @property
    def completed_orders_count(self):
        """Get number of completed orders."""
        return self.orders.filter(
            status='delivered',
            deleted_at__isnull=True
        ).count()
    
    @property
    def success_rate(self):
        """Calculate order success rate."""
        total = self.total_orders_count
        if total == 0:
            return 0
        completed = self.completed_orders_count
        return (completed / total) * 100
    
    def get_latest_prices(self, days=7):
        """Get latest prices submitted by this farmer."""
        from django.utils import timezone
        from datetime import timedelta
        
        cutoff_date = timezone.now().date() - timedelta(days=days)
        return self.farmer_prices.filter(
            date__gte=cutoff_date,
            deleted_at__isnull=True
        ).select_related('sku').order_by('-date', 'sku__name')


class FarmerDocument(BaseModel):
    """Documents uploaded by farmers for verification."""
    
    DOCUMENT_TYPES = [
        ('aadhar', _('Aadhar Card')),
        ('pan', _('PAN Card')),
        ('bank_passbook', _('Bank Passbook')),
        ('land_document', _('Land Document')),
        ('other', _('Other')),
    ]
    
    farmer = models.ForeignKey(
        Farmer,
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name=_('Farmer')
    )
    document_type = models.CharField(
        max_length=20,
        choices=DOCUMENT_TYPES,
        verbose_name=_('Document Type')
    )
    document_file = models.FileField(
        upload_to='farmer_documents/',
        verbose_name=_('Document File')
    )
    document_number = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Document Number')
    )
    is_verified = models.BooleanField(
        default=False,
        verbose_name=_('Is Verified')
    )
    verified_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Verified At')
    )
    verified_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_documents',
        verbose_name=_('Verified By')
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_('Verification Notes')
    )
    
    class Meta:
        verbose_name = _('Farmer Document')
        verbose_name_plural = _('Farmer Documents')
        unique_together = ['farmer', 'document_type']
        
    def __str__(self):
        return f"{self.farmer.farmer_id} - {self.get_document_type_display()}"
