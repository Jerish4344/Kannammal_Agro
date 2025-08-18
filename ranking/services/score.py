"""Farmer ranking computation service."""

from decimal import Decimal
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from django.db import models
from django.db.models import Avg, Count, Sum, Q, F, Window
from django.db.models.functions import PercentRank
from django.utils import timezone
from django.conf import settings

from farmers.models import Farmer
from pricing.models import FarmerPrice
from orders.models import Order
from regions.models import Region
from ranking.models import FarmerScore, RankingConfiguration


class FarmerRankingService:
    """Service for computing farmer rankings and scores."""
    
    def __init__(self, config: Optional[RankingConfiguration] = None):
        """Initialize with ranking configuration."""
        self.config = config or self._get_default_config()
        self.weights = {
            'price': self.config.price_weight,
            'consistency': self.config.consistency_weight,
            'reliability': self.config.reliability_weight,
            'fill': self.config.fill_rate_weight,
        }
    
    def _get_default_config(self) -> RankingConfiguration:
        """Get default ranking configuration."""
        config, created = RankingConfiguration.objects.get_or_create(
            name='default',
            defaults={
                'price_weight': Decimal('0.4'),
                'consistency_weight': Decimal('0.25'),
                'reliability_weight': Decimal('0.25'),
                'fill_rate_weight': Decimal('0.1'),
                'evaluation_window_days': 30,
                'min_submissions_required': 5,
                'is_active': True,
            }
        )
        return config
    
    def compute_price_competitiveness(self, farmer: Farmer, window_start: datetime.date, window_end: datetime.date) -> Decimal:
        """
        Compute price competitiveness score (0-100).
        Higher score for more competitive (lower) prices.
        """
        # Get farmer's prices in the window
        farmer_prices = FarmerPrice.objects.filter(
            farmer=farmer,
            date__range=[window_start, window_end],
            deleted_at__isnull=True,
            is_active=True
        ).values('sku', 'region').annotate(
            avg_price=Avg('price')
        )
        
        if not farmer_prices:
            return Decimal('0')
        
        total_score = Decimal('0')
        sku_count = 0
        
        for fp in farmer_prices:
            # Get median price for same SKU and region in the window
            median_price = FarmerPrice.objects.filter(
                sku_id=fp['sku'],
                region_id=fp['region'],
                date__range=[window_start, window_end],
                deleted_at__isnull=True,
                is_active=True
            ).aggregate(
                median=models.functions.Percentile('price', 0.5)
            )['median']
            
            if median_price and median_price > 0:
                # Score inversely related to price
                # If farmer's price is lower than median, score is higher
                price_ratio = fp['avg_price'] / median_price
                if price_ratio <= 0.8:  # 20% below median
                    score = Decimal('100')
                elif price_ratio <= 0.9:  # 10% below median
                    score = Decimal('85')
                elif price_ratio <= 1.0:  # At or below median
                    score = Decimal('70')
                elif price_ratio <= 1.1:  # 10% above median
                    score = Decimal('50')
                elif price_ratio <= 1.2:  # 20% above median
                    score = Decimal('30')
                else:  # More than 20% above median
                    score = Decimal('10')
                
                total_score += score
                sku_count += 1
        
        return total_score / sku_count if sku_count > 0 else Decimal('0')
    
    def compute_consistency(self, farmer: Farmer, window_start: datetime.date, window_end: datetime.date) -> Decimal:
        """
        Compute consistency score (0-100).
        Based on percentage of days farmer submitted prices on time.
        """
        cutoff_hour = getattr(settings, 'PRICE_CUTOFF_HOUR', 9)
        
        # Count total submissions and on-time submissions
        submissions = FarmerPrice.objects.filter(
            farmer=farmer,
            date__range=[window_start, window_end],
            deleted_at__isnull=True
        ).values('date').annotate(
            on_time=Count('id', filter=Q(submitted_at__hour__lt=cutoff_hour))
        )
        
        total_days = len(submissions)
        if total_days == 0:
            return Decimal('0')
        
        on_time_days = sum(1 for s in submissions if s['on_time'] > 0)
        consistency_rate = (on_time_days / total_days) * 100
        
        return Decimal(str(consistency_rate))
    
    def compute_reliability(self, farmer: Farmer, window_start: datetime.date, window_end: datetime.date) -> Decimal:
        """
        Compute delivery reliability score (0-100).
        Based on on-time delivery percentage over last 90 days.
        """
        # Use last 90 days for delivery reliability
        cutoff_date = window_end - timedelta(days=90)
        
        orders = Order.objects.filter(
            farmer=farmer,
            created_at__date__gte=cutoff_date,
            created_at__date__lte=window_end,
            status='delivered',
            deleted_at__isnull=True
        )
        
        total_orders = orders.count()
        if total_orders == 0:
            return Decimal('50')  # Neutral score for new farmers
        
        on_time_orders = orders.filter(
            actual_delivery_date__lte=F('expected_delivery_date')
        ).count()
        
        reliability_rate = (on_time_orders / total_orders) * 100
        return Decimal(str(reliability_rate))
    
    def compute_fill_rate(self, farmer: Farmer, window_start: datetime.date, window_end: datetime.date) -> Decimal:
        """
        Compute order fill rate score (0-100).
        Based on fulfilled quantity vs ordered quantity over last 90 days.
        """
        # Use last 90 days for fill rate
        cutoff_date = window_end - timedelta(days=90)
        
        orders = Order.objects.filter(
            farmer=farmer,
            created_at__date__gte=cutoff_date,
            created_at__date__lte=window_end,
            status='delivered',
            deleted_at__isnull=True,
            delivered_quantity__isnull=False
        ).aggregate(
            total_ordered=Sum('quantity'),
            total_delivered=Sum('delivered_quantity')
        )
        
        total_ordered = orders['total_ordered'] or Decimal('0')
        total_delivered = orders['total_delivered'] or Decimal('0')
        
        if total_ordered == 0:
            return Decimal('50')  # Neutral score for new farmers
        
        fill_rate = (total_delivered / total_ordered) * 100
        return min(Decimal('100'), fill_rate)  # Cap at 100%
    
    def compute_total_score(self, farmer: Farmer, window_start: datetime.date, window_end: datetime.date) -> Dict:
        """Compute total weighted score for a farmer."""
        
        # Check if farmer has minimum required submissions
        submission_count = FarmerPrice.objects.filter(
            farmer=farmer,
            date__range=[window_start, window_end],
            deleted_at__isnull=True
        ).count()
        
        if submission_count < self.config.min_submissions_required:
            return {
                'price_competitiveness': Decimal('0'),
                'consistency_score': Decimal('0'),
                'reliability_score': Decimal('0'),
                'fill_rate_score': Decimal('0'),
                'total_score': Decimal('0'),
                'total_submissions': submission_count,
                'insufficient_data': True
            }
        
        # Compute individual metric scores
        price_score = self.compute_price_competitiveness(farmer, window_start, window_end)
        consistency_score = self.compute_consistency(farmer, window_start, window_end)
        reliability_score = self.compute_reliability(farmer, window_start, window_end)
        fill_rate_score = self.compute_fill_rate(farmer, window_start, window_end)
        
        # Calculate weighted total score
        total_score = (
            price_score * self.weights['price'] +
            consistency_score * self.weights['consistency'] +
            reliability_score * self.weights['reliability'] +
            fill_rate_score * self.weights['fill']
        )
        
        # Clamp to 0-100 range
        total_score = max(Decimal('0'), min(Decimal('100'), total_score))
        
        return {
            'price_competitiveness': price_score,
            'consistency_score': consistency_score,
            'reliability_score': reliability_score,
            'fill_rate_score': fill_rate_score,
            'total_score': total_score,
            'total_submissions': submission_count,
            'insufficient_data': False
        }
    
    def compute_supporting_metrics(self, farmer: Farmer, window_start: datetime.date, window_end: datetime.date) -> Dict:
        """Compute supporting metrics for the score calculation."""
        
        # Price submission metrics
        price_metrics = FarmerPrice.objects.filter(
            farmer=farmer,
            date__range=[window_start, window_end],
            deleted_at__isnull=True
        ).aggregate(
            total_submissions=Count('id'),
            on_time_submissions=Count('id', filter=Q(
                submitted_at__hour__lt=getattr(settings, 'PRICE_CUTOFF_HOUR', 9)
            ))
        )
        
        # Order metrics (last 90 days)
        cutoff_date = window_end - timedelta(days=90)
        order_metrics = Order.objects.filter(
            farmer=farmer,
            created_at__date__gte=cutoff_date,
            created_at__date__lte=window_end,
            deleted_at__isnull=True
        ).aggregate(
            total_orders=Count('id'),
            delivered_orders=Count('id', filter=Q(status='delivered')),
            on_time_deliveries=Count('id', filter=Q(
                status='delivered',
                actual_delivery_date__lte=F('expected_delivery_date')
            )),
            total_ordered_quantity=Sum('quantity'),
            total_delivered_quantity=Sum('delivered_quantity', filter=Q(status='delivered'))
        )
        
        return {
            'total_prices_submitted': price_metrics['total_submissions'] or 0,
            'on_time_submissions': price_metrics['on_time_submissions'] or 0,
            'total_orders': order_metrics['total_orders'] or 0,
            'on_time_deliveries': order_metrics['on_time_deliveries'] or 0,
            'total_quantity_ordered': order_metrics['total_ordered_quantity'] or Decimal('0'),
            'total_quantity_delivered': order_metrics['total_delivered_quantity'] or Decimal('0'),
        }
    
    def compute_farmer_score(self, farmer: Farmer, window_start: datetime.date, window_end: datetime.date) -> FarmerScore:
        """Compute and save farmer score."""
        
        scores = self.compute_total_score(farmer, window_start, window_end)
        metrics = self.compute_supporting_metrics(farmer, window_start, window_end)
        
        # Create or update farmer score
        farmer_score, created = FarmerScore.objects.update_or_create(
            farmer=farmer,
            region=farmer.region,
            window_start=window_start,
            window_end=window_end,
            defaults={
                'price_competitiveness': scores['price_competitiveness'],
                'consistency_score': scores['consistency_score'],
                'reliability_score': scores['reliability_score'],
                'fill_rate_score': scores['fill_rate_score'],
                'total_score': scores['total_score'],
                'total_prices_submitted': metrics['total_prices_submitted'],
                'on_time_submissions': metrics['on_time_submissions'],
                'total_orders': metrics['total_orders'],
                'on_time_deliveries': metrics['on_time_deliveries'],
                'total_quantity_ordered': metrics['total_quantity_ordered'],
                'total_quantity_delivered': metrics['total_quantity_delivered'],
                'is_current': True,
            }
        )
        
        return farmer_score
    
    def compute_all_farmers_scores(self, region: Optional[Region] = None, window_start: Optional[datetime.date] = None, window_end: Optional[datetime.date] = None) -> List[FarmerScore]:
        """Compute scores for all farmers in a region."""
        
        if not window_end:
            window_end = timezone.now().date()
        if not window_start:
            window_start = window_end - timedelta(days=self.config.evaluation_window_days)
        
        # Get farmers to evaluate
        farmers_query = Farmer.objects.filter(
            is_active=True,
            deleted_at__isnull=True
        )
        
        if region:
            farmers_query = farmers_query.filter(region=region)
        
        farmers = farmers_query.select_related('region')
        
        # Mark previous scores as not current
        FarmerScore.objects.filter(
            farmer__in=farmers,
            is_current=True
        ).update(is_current=False)
        
        # Compute new scores
        scores = []
        for farmer in farmers:
            score = self.compute_farmer_score(farmer, window_start, window_end)
            scores.append(score)
        
        return scores
    
    def get_farmer_rankings(self, region: Optional[Region] = None, limit: Optional[int] = None) -> models.QuerySet:
        """Get current farmer rankings."""
        
        queryset = FarmerScore.objects.filter(
            is_current=True,
            deleted_at__isnull=True
        ).select_related('farmer', 'region').order_by('-total_score', 'farmer__farmer_id')
        
        if region:
            queryset = queryset.filter(region=region)
        
        if limit:
            queryset = queryset[:limit]
        
        return queryset
