"""Pricing models for farmer price submissions."""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator

from core.models import BaseModel


class FarmerPrice(BaseModel):
    """Daily price submissions by farmers for SKUs."""
    
    SUBMISSION_METHODS = [
        ('voice', _('Voice Input')),
        ('text', _('Text Input')),
        ('upload', _('File Upload')),
    ]
    
    farmer = models.ForeignKey(
        'farmers.Farmer',
        on_delete=models.CASCADE,
        related_name='farmer_prices',
        verbose_name=_('Farmer')
    )
    sku = models.ForeignKey(
        'catalog.SKU',
        on_delete=models.CASCADE,
        related_name='farmer_prices',
        verbose_name=_('SKU')
    )
    region = models.ForeignKey(
        'regions.Region',
        on_delete=models.CASCADE,
        related_name='farmer_prices',
        verbose_name=_('Region')
    )
    date = models.DateField(
        verbose_name=_('Price Date')
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        verbose_name=_('Price per Unit')
    )
    quantity_available = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0.01)],
        verbose_name=_('Quantity Available')
    )
    submitted_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Submitted At')
    )
    submitted_via = models.CharField(
        max_length=10,
        choices=SUBMISSION_METHODS,
        default='text',
        verbose_name=_('Submission Method')
    )
    voice_transcript = models.TextField(
        blank=True,
        verbose_name=_('Voice Transcript')
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_('Additional Notes')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Is Active')
    )
    
    class Meta:
        verbose_name = _('Farmer Price')
        verbose_name_plural = _('Farmer Prices')
        unique_together = ['farmer', 'sku', 'date']
        ordering = ['-date', 'sku__name', 'price']
        indexes = [
            models.Index(fields=['sku', 'region', 'date']),
        ]
        
    def __str__(self):
        return f"{self.farmer} - {self.sku.name} - ₹{self.price} ({self.date})"
    
    def save(self, *args, **kwargs):
        """Auto-set region based on farmer's region if not provided and handle date."""
        from django.utils import timezone
        
        # Auto-set region based on farmer's region if not provided
        if not self.region_id and self.farmer_id:
            self.region = self.farmer.region
        
        # Set default date to today if not provided
        if not self.date:
            self.date = timezone.now().date()
            
        super().save(*args, **kwargs)
    
    @property
    def is_on_time(self):
        """Check if price was submitted on time (before cutoff hour)."""
        from django.conf import settings
        cutoff_hour = getattr(settings, 'PRICE_CUTOFF_HOUR', 9)
        return self.submitted_at.hour < cutoff_hour
    
    @property
    def ranking_info(self):
        """Get ranking information for this price submission."""
        # Get all prices for same SKU, region, and date
        all_prices = FarmerPrice.objects.filter(
            sku=self.sku,
            region=self.region,
            date=self.date,
            deleted_at__isnull=True,
            is_active=True
        ).order_by('price')
        
        prices_list = list(all_prices.values_list('price', flat=True))
        
        if not prices_list:
            return {'rank': 'N/A', 'total': 0, 'is_lowest': False, 'is_highest': False}
        
        rank = prices_list.index(self.price) + 1
        total = len(prices_list)
        is_lowest = self.price == min(prices_list)
        is_highest = self.price == max(prices_list)
        
        return {
            'rank': rank,
            'total': total,
            'is_lowest': is_lowest,
            'is_highest': is_highest,
            'percentile': (total - rank + 1) / total * 100
        }


class PriceHistory(models.Model):
    """Historical price data for market analysis."""
    
    sku = models.ForeignKey(
        'catalog.SKU',
        on_delete=models.CASCADE,
        related_name='price_history',
        verbose_name=_('SKU')
    )
    region = models.ForeignKey(
        'regions.Region',
        on_delete=models.CASCADE,
        related_name='price_history',
        verbose_name=_('Region')
    )
    date = models.DateField(verbose_name=_('Date'))
    min_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Minimum Price')
    )
    max_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Maximum Price')
    )
    avg_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Average Price')
    )
    median_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Median Price')
    )
    total_submissions = models.IntegerField(
        default=0,
        verbose_name=_('Total Submissions')
    )
    total_quantity = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        verbose_name=_('Total Quantity Available')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Price History')
        verbose_name_plural = _('Price Histories')
        unique_together = ['sku', 'region', 'date']
        ordering = ['-date']
        
    def __str__(self):
        return f"{self.sku.name} - {self.region.name} - {self.date}"
