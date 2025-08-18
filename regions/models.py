"""Region models for Kannammal Agro."""

from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models import BaseModel


class Region(BaseModel):
    """Geographic regions for organizing farmers and operations."""
    
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_('Region Name')
    )
    code = models.CharField(
        max_length=10,
        unique=True,
        verbose_name=_('Region Code')
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('Description')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Is Active')
    )
    
    class Meta:
        verbose_name = _('Region')
        verbose_name_plural = _('Regions')
        ordering = ['name']
        
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    @property
    def active_farmers_count(self):
        """Get count of active farmers in this region."""
        return self.farmers.filter(deleted_at__isnull=True, is_active=True).count()
    
    @property
    def total_orders_count(self):
        """Get total orders count for this region."""
        return self.orders.filter(deleted_at__isnull=True).count()
