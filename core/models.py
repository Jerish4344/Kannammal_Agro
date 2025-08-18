"""Core models and utilities for Kannammal Agro."""

from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    """Abstract base model with timestamp fields."""
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SoftDeleteModel(models.Model):
    """Abstract base model with soft delete functionality."""
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_deleted_by'
    )

    class Meta:
        abstract = True

    def soft_delete(self, user=None):
        """Mark the object as deleted."""
        self.deleted_at = timezone.now()
        self.deleted_by = user
        self.save()

    def restore(self):
        """Restore the object."""
        self.deleted_at = None
        self.deleted_by = None
        self.save()

    @property
    def is_deleted(self):
        return self.deleted_at is not None


class BaseModel(TimeStampedModel, SoftDeleteModel):
    """Base model with timestamp and soft delete functionality."""
    
    class Meta:
        abstract = True
