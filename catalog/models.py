"""Catalog models for fruits and vegetables SKUs."""

from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models import BaseModel


class SKU(BaseModel):
    """Stock Keeping Unit for fruits and vegetables."""
    
    UNIT_CHOICES = [
        ('kg', _('Kilogram')),
        ('gram', _('Gram')),
        ('quintal', _('Quintal')),
        ('ton', _('Ton')),
        ('piece', _('Piece')),
        ('dozen', _('Dozen')),
        ('bundle', _('Bundle')),
    ]
    
    CATEGORY_CHOICES = [
        ('fruit', _('Fruit')),
        ('vegetable', _('Vegetable')),
        ('grain', _('Grain')),
        ('spice', _('Spice')),
        ('other', _('Other')),
    ]
    
    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name=_('SKU Code')
    )
    name = models.CharField(
        max_length=100,
        verbose_name=_('Product Name')
    )
    name_ta = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Product Name (Tamil)')
    )
    name_hi = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Product Name (Hindi)')
    )
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='vegetable',
        verbose_name=_('Category')
    )
    unit = models.CharField(
        max_length=20,
        choices=UNIT_CHOICES,
        default='kg',
        verbose_name=_('Unit of Measurement')
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('Description')
    )
    image = models.ImageField(
        upload_to='sku_images/',
        null=True,
        blank=True,
        verbose_name=_('Product Image')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Is Active')
    )
    min_order_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=1.0,
        verbose_name=_('Minimum Order Quantity')
    )
    
    class Meta:
        verbose_name = _('SKU')
        verbose_name_plural = _('SKUs')
        ordering = ['category', 'name']
        
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def get_localized_name(self, language='en'):
        """Get product name in specified language."""
        if language == 'ta' and self.name_ta:
            return self.name_ta
        elif language == 'hi' and self.name_hi:
            return self.name_hi
        return self.name
    
    @property
    def latest_price_by_region(self):
        """Get latest prices for this SKU grouped by region."""
        from pricing.models import FarmerPrice
        from django.utils import timezone
        from datetime import timedelta
        
        # Get prices from last 7 days
        cutoff_date = timezone.now().date() - timedelta(days=7)
        
        return FarmerPrice.objects.filter(
            sku=self,
            date__gte=cutoff_date,
            deleted_at__isnull=True
        ).select_related('farmer', 'region').order_by('region', '-date', 'price')


class SKUImage(BaseModel):
    """Additional images for SKUs."""
    
    sku = models.ForeignKey(
        SKU,
        on_delete=models.CASCADE,
        related_name='additional_images',
        verbose_name=_('SKU')
    )
    image = models.ImageField(
        upload_to='sku_images/',
        verbose_name=_('Image')
    )
    caption = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Caption')
    )
    is_primary = models.BooleanField(
        default=False,
        verbose_name=_('Is Primary Image')
    )
    
    class Meta:
        verbose_name = _('SKU Image')
        verbose_name_plural = _('SKU Images')
        
    def __str__(self):
        return f"Image for {self.sku.name}"
