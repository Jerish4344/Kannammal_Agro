"""Farmer ranking system models."""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator

from core.models import BaseModel


class FarmerScore(BaseModel):
    """Farmer ranking scores with metrics breakdown."""
    
    farmer = models.ForeignKey(
        'farmers.Farmer',
        on_delete=models.CASCADE,
        related_name='scores',
        verbose_name=_('Farmer')
    )
    region = models.ForeignKey(
        'regions.Region',
        on_delete=models.CASCADE,
        related_name='farmer_scores',
        verbose_name=_('Region')
    )
    window_start = models.DateField(
        verbose_name=_('Evaluation Period Start')
    )
    window_end = models.DateField(
        verbose_name=_('Evaluation Period End')
    )
    
    # Metric scores (0-100)
    price_competitiveness = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name=_('Price Competitiveness Score')
    )
    consistency_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name=_('Consistency Score')
    )
    reliability_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name=_('Delivery Reliability Score')
    )
    fill_rate_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name=_('Order Fill Rate Score')
    )
    
    # Weighted total score
    total_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name=_('Total Weighted Score')
    )
    
    # Supporting metrics
    total_prices_submitted = models.IntegerField(
        default=0,
        verbose_name=_('Total Prices Submitted')
    )
    on_time_submissions = models.IntegerField(
        default=0,
        verbose_name=_('On Time Submissions')
    )
    total_orders = models.IntegerField(
        default=0,
        verbose_name=_('Total Orders')
    )
    on_time_deliveries = models.IntegerField(
        default=0,
        verbose_name=_('On Time Deliveries')
    )
    total_quantity_ordered = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        verbose_name=_('Total Quantity Ordered')
    )
    total_quantity_delivered = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        verbose_name=_('Total Quantity Delivered')
    )
    
    computed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Computed At')
    )
    is_current = models.BooleanField(
        default=True,
        verbose_name=_('Is Current Score')
    )
    
    class Meta:
        verbose_name = _('Farmer Score')
        verbose_name_plural = _('Farmer Scores')
        ordering = ['-total_score', '-computed_at']
        indexes = [
            models.Index(fields=['farmer', 'is_current']),
            models.Index(fields=['region', 'is_current', 'total_score']),
            models.Index(fields=['window_start', 'window_end']),
        ]
        
    def __str__(self):
        return f"{self.farmer.farmer_id} - Score: {self.total_score} ({self.window_start} to {self.window_end})"
    
    @property
    def rank_in_region(self):
        """Get farmer's rank in their region."""
        better_scores = FarmerScore.objects.filter(
            region=self.region,
            is_current=True,
            total_score__gt=self.total_score,
            deleted_at__isnull=True
        ).count()
        return better_scores + 1
    
    @property
    def percentile_in_region(self):
        """Get farmer's percentile in their region."""
        total_farmers = FarmerScore.objects.filter(
            region=self.region,
            is_current=True,
            deleted_at__isnull=True
        ).count()
        
        if total_farmers == 0:
            return 0
        
        rank = self.rank_in_region
        return ((total_farmers - rank + 1) / total_farmers) * 100
    
    @property
    def badge(self):
        """Get farmer's performance badge."""
        percentile = self.percentile_in_region
        if percentile >= 90:
            return 'top_10'
        elif percentile >= 75:
            return 'excellent'
        elif percentile >= 50:
            return 'good'
        elif percentile >= 25:
            return 'average'
        else:
            return 'needs_improvement'
    
    def get_trend(self, days=7):
        """Get score trend compared to previous period."""
        from django.utils import timezone
        from datetime import timedelta
        
        cutoff_date = timezone.now().date() - timedelta(days=days)
        
        previous_score = FarmerScore.objects.filter(
            farmer=self.farmer,
            computed_at__date__lt=cutoff_date,
            deleted_at__isnull=True
        ).order_by('-computed_at').first()
        
        if not previous_score:
            return 'new'
        
        diff = self.total_score - previous_score.total_score
        if diff > 5:
            return 'rising'
        elif diff < -5:
            return 'falling'
        else:
            return 'stable'


class RankingConfiguration(models.Model):
    """Configuration for ranking system weights and parameters."""
    
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_('Configuration Name')
    )
    price_weight = models.DecimalField(
        max_digits=4,
        decimal_places=3,
        default=0.4,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        verbose_name=_('Price Competitiveness Weight')
    )
    consistency_weight = models.DecimalField(
        max_digits=4,
        decimal_places=3,
        default=0.25,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        verbose_name=_('Consistency Weight')
    )
    reliability_weight = models.DecimalField(
        max_digits=4,
        decimal_places=3,
        default=0.25,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        verbose_name=_('Reliability Weight')
    )
    fill_rate_weight = models.DecimalField(
        max_digits=4,
        decimal_places=3,
        default=0.1,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        verbose_name=_('Fill Rate Weight')
    )
    evaluation_window_days = models.IntegerField(
        default=30,
        verbose_name=_('Evaluation Window (Days)')
    )
    min_submissions_required = models.IntegerField(
        default=5,
        verbose_name=_('Minimum Submissions Required')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Is Active Configuration')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Ranking Configuration')
        verbose_name_plural = _('Ranking Configurations')
        
    def __str__(self):
        return self.name
    
    def clean(self):
        """Validate that weights sum to 1.0."""
        from django.core.exceptions import ValidationError
        
        total_weight = (
            self.price_weight + 
            self.consistency_weight + 
            self.reliability_weight + 
            self.fill_rate_weight
        )
        
        if abs(total_weight - 1.0) > 0.001:  # Allow for floating point precision
            raise ValidationError(_('Weights must sum to 1.0'))


class FarmerScoreHistory(models.Model):
    """Historical tracking of farmer score changes."""
    
    farmer = models.ForeignKey(
        'farmers.Farmer',
        on_delete=models.CASCADE,
        related_name='score_history',
        verbose_name=_('Farmer')
    )
    date = models.DateField(verbose_name=_('Score Date'))
    total_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name=_('Total Score')
    )
    rank_in_region = models.IntegerField(
        verbose_name=_('Rank in Region')
    )
    total_farmers_in_region = models.IntegerField(
        verbose_name=_('Total Farmers in Region')
    )
    
    class Meta:
        verbose_name = _('Farmer Score History')
        verbose_name_plural = _('Farmer Score Histories')
        unique_together = ['farmer', 'date']
        ordering = ['-date']
        
    def __str__(self):
        return f"{self.farmer.farmer_id} - {self.date} - Score: {self.total_score}"
