"""User accounts and RBAC models for Kannammal Agro."""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models import BaseModel


class User(AbstractUser):
    """Custom user model with role-based access control."""
    
    ROLE_CHOICES = [
        ('admin', _('Admin')),
        ('region_head', _('Region Head')),
        ('buyer_head', _('Buyer Head')),
        ('buyer', _('Buyer')),
        ('farmer', _('Farmer')),
    ]
    
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='farmer',
        verbose_name=_('Role')
    )
    region = models.ForeignKey(
        'regions.Region',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='users',
        verbose_name=_('Region')
    )
    phone = models.CharField(
        max_length=15,
        blank=True,
        verbose_name=_('Phone Number')
    )
    preferred_language = models.CharField(
        max_length=5,
        choices=[
            ('en', 'English'),
            ('ta', 'தமிழ்'),
            ('hi', 'हिन्दी'),
        ],
        default='en',
        verbose_name=_('Preferred Language')
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    @property
    def is_admin(self):
        return self.role == 'admin'
    
    @property
    def is_region_head(self):
        return self.role == 'region_head'
    
    @property
    def is_buyer_head(self):
        return self.role == 'buyer_head'
    
    @property
    def is_buyer(self):
        return self.role == 'buyer'
    
    @property
    def is_farmer(self):
        return self.role == 'farmer'
    
    def can_access_region(self, region):
        """Check if user can access data for a specific region."""
        if self.is_admin:
            return True
        return self.region == region
    
    def get_accessible_regions(self):
        """Get regions this user can access."""
        from regions.models import Region
        if self.is_admin:
            return Region.objects.all()
        elif self.region:
            return Region.objects.filter(id=self.region.id)
        return Region.objects.none()


class UserProfile(BaseModel):
    """Extended user profile information."""
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name=_('User')
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        null=True,
        blank=True,
        verbose_name=_('Avatar')
    )
    bio = models.TextField(
        blank=True,
        verbose_name=_('Bio')
    )
    address = models.TextField(
        blank=True,
        verbose_name=_('Address')
    )
    emergency_contact = models.CharField(
        max_length=15,
        blank=True,
        verbose_name=_('Emergency Contact')
    )
    
    class Meta:
        verbose_name = _('User Profile')
        verbose_name_plural = _('User Profiles')
        
    def __str__(self):
        return f"Profile for {self.user.username}"


class AuditLog(models.Model):
    """Audit log for tracking user actions."""
    
    ACTION_CHOICES = [
        ('create', _('Create')),
        ('read', _('Read')),
        ('update', _('Update')),
        ('delete', _('Delete')),
        ('login', _('Login')),
        ('logout', _('Logout')),
        ('order_view', _('Order View')),
        ('order_confirm', _('Order Confirm')),
        ('price_submit', _('Price Submit')),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='audit_logs',
        verbose_name=_('User')
    )
    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        verbose_name=_('Action')
    )
    content_type = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Content Type')
    )
    object_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Object ID')
    )
    details = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Details')
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=_('IP Address')
    )
    user_agent = models.TextField(
        blank=True,
        verbose_name=_('User Agent')
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Audit Log')
        verbose_name_plural = _('Audit Logs')
        ordering = ['-timestamp']
        
    def __str__(self):
        return f"{self.user.username} - {self.get_action_display()} at {self.timestamp}"
