"""Notification models for SMS, WhatsApp, and email."""

from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models import BaseModel


class MessageLog(BaseModel):
    """Log of all notifications sent."""
    
    MESSAGE_TYPES = [
        ('sms', _('SMS')),
        ('whatsapp', _('WhatsApp')),
        ('email', _('Email')),
        ('push', _('Push Notification')),
    ]
    
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('sent', _('Sent')),
        ('delivered', _('Delivered')),
        ('failed', _('Failed')),
        ('read', _('Read')),
    ]
    
    recipient = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='received_messages',
        verbose_name=_('Recipient')
    )
    message_type = models.CharField(
        max_length=10,
        choices=MESSAGE_TYPES,
        verbose_name=_('Message Type')
    )
    subject = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Subject')
    )
    message = models.TextField(verbose_name=_('Message Content'))
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name=_('Status')
    )
    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Sent At')
    )
    delivered_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Delivered At')
    )
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Read At')
    )
    external_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('External Message ID')
    )
    error_message = models.TextField(
        blank=True,
        verbose_name=_('Error Message')
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Additional Metadata')
    )
    
    class Meta:
        verbose_name = _('Message Log')
        verbose_name_plural = _('Message Logs')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'status']),
            models.Index(fields=['message_type', 'status']),
            models.Index(fields=['created_at']),
        ]
        
    def __str__(self):
        return f"{self.get_message_type_display()} to {self.recipient.username} - {self.status}"


class NotificationTemplate(BaseModel):
    """Templates for different types of notifications."""
    
    TEMPLATE_TYPES = [
        ('order_placed', _('Order Placed')),
        ('order_confirmed', _('Order Confirmed')),
        ('order_ready', _('Order Ready')),
        ('order_cancelled', _('Order Cancelled')),
        ('price_reminder', _('Price Submission Reminder')),
        ('payment_completed', _('Payment Completed')),
        ('farmer_verification', _('Farmer Verification')),
        ('low_ranking_alert', _('Low Ranking Alert')),
    ]
    
    name = models.CharField(
        max_length=50,
        choices=TEMPLATE_TYPES,
        unique=True,
        verbose_name=_('Template Name')
    )
    subject_en = models.CharField(
        max_length=200,
        verbose_name=_('Subject (English)')
    )
    subject_ta = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Subject (Tamil)')
    )
    subject_hi = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Subject (Hindi)')
    )
    message_en = models.TextField(verbose_name=_('Message (English)'))
    message_ta = models.TextField(
        blank=True,
        verbose_name=_('Message (Tamil)')
    )
    message_hi = models.TextField(
        blank=True,
        verbose_name=_('Message (Hindi)')
    )
    sms_template_en = models.TextField(
        blank=True,
        verbose_name=_('SMS Template (English)')
    )
    sms_template_ta = models.TextField(
        blank=True,
        verbose_name=_('SMS Template (Tamil)')
    )
    sms_template_hi = models.TextField(
        blank=True,
        verbose_name=_('SMS Template (Hindi)')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Is Active')
    )
    
    class Meta:
        verbose_name = _('Notification Template')
        verbose_name_plural = _('Notification Templates')
        
    def __str__(self):
        return self.get_name_display()
    
    def get_localized_subject(self, language='en'):
        """Get subject in specified language."""
        if language == 'ta' and self.subject_ta:
            return self.subject_ta
        elif language == 'hi' and self.subject_hi:
            return self.subject_hi
        return self.subject_en
    
    def get_localized_message(self, language='en'):
        """Get message in specified language."""
        if language == 'ta' and self.message_ta:
            return self.message_ta
        elif language == 'hi' and self.message_hi:
            return self.message_hi
        return self.message_en
    
    def get_localized_sms(self, language='en'):
        """Get SMS template in specified language."""
        if language == 'ta' and self.sms_template_ta:
            return self.sms_template_ta
        elif language == 'hi' and self.sms_template_hi:
            return self.sms_template_hi
        return self.sms_template_en or self.get_localized_message(language)


class NotificationPreference(BaseModel):
    """User preferences for notifications."""
    
    user = models.OneToOneField(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='notification_preferences',
        verbose_name=_('User')
    )
    email_enabled = models.BooleanField(
        default=True,
        verbose_name=_('Email Notifications')
    )
    sms_enabled = models.BooleanField(
        default=True,
        verbose_name=_('SMS Notifications')
    )
    whatsapp_enabled = models.BooleanField(
        default=False,
        verbose_name=_('WhatsApp Notifications')
    )
    push_enabled = models.BooleanField(
        default=True,
        verbose_name=_('Push Notifications')
    )
    order_notifications = models.BooleanField(
        default=True,
        verbose_name=_('Order Notifications')
    )
    price_reminders = models.BooleanField(
        default=True,
        verbose_name=_('Price Submission Reminders')
    )
    ranking_alerts = models.BooleanField(
        default=True,
        verbose_name=_('Ranking Alerts')
    )
    marketing_messages = models.BooleanField(
        default=False,
        verbose_name=_('Marketing Messages')
    )
    
    class Meta:
        verbose_name = _('Notification Preference')
        verbose_name_plural = _('Notification Preferences')
        
    def __str__(self):
        return f"Preferences for {self.user.username}"
