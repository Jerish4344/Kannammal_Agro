"""
Management command to recompute farmer rankings.
This command should be run nightly via cron job.
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from django.conf import settings
import logging

from farmers.models import Farmer
from ranking.models import FarmerScore
from ranking.services.score import compute_total_score

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Recompute farmer rankings and scores for all farmers'

    def add_arguments(self, parser):
        parser.add_argument(
            '--region',
            type=str,
            help='Compute rankings for specific region only',
        )
        parser.add_argument(
            '--farmer-id',
            type=int,
            help='Compute ranking for specific farmer only',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recomputation even if recent scores exist',
        )

    def handle(self, *args, **options):
        start_time = timezone.now()
        self.stdout.write(
            self.style.SUCCESS(f'Starting farmer ranking recomputation at {start_time}')
        )

        try:
            # Determine which farmers to process
            farmers_qs = Farmer.objects.select_related('user', 'region')
            
            if options['region']:
                farmers_qs = farmers_qs.filter(region__code=options['region'])
                self.stdout.write(f"Filtering to region: {options['region']}")
            
            if options['farmer_id']:
                farmers_qs = farmers_qs.filter(id=options['farmer_id'])
                self.stdout.write(f"Processing single farmer ID: {options['farmer_id']}")

            farmers = list(farmers_qs)
            
            if not farmers:
                self.stdout.write(
                    self.style.WARNING('No farmers found matching criteria')
                )
                return

            self.stdout.write(f'Found {len(farmers)} farmers to process')

            # Check if we need to force recomputation
            if not options['force']:
                recent_threshold = timezone.now() - timezone.timedelta(hours=23)
                recent_scores = FarmerScore.objects.filter(
                    computed_at__gte=recent_threshold
                ).count()
                
                if recent_scores > 0:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Found {recent_scores} scores computed in last 23 hours. '
                            'Use --force to override.'
                        )
                    )
                    return

            updated_count = 0
            error_count = 0

            with transaction.atomic():
                for farmer in farmers:
                    try:
                        # Compute new score
                        score_data = compute_total_score(farmer)
                        
                        if options['dry_run']:
                            self.stdout.write(
                                f'DRY RUN - Would update {farmer.user.get_full_name()}: '
                                f'Score {score_data["total_score"]:.2f}'
                            )
                            continue

                        # Update or create farmer score
                        farmer_score, created = FarmerScore.objects.update_or_create(
                            farmer=farmer,
                            defaults={
                                'total_score': score_data['total_score'],
                                'price_score': score_data['price_score'],
                                'quality_score': score_data['quality_score'],
                                'reliability_score': score_data['reliability_score'],
                                'volume_score': score_data['volume_score'],
                                'response_time_score': score_data['response_time_score'],
                                'computed_at': timezone.now(),
                                'score_metadata': {
                                    'weights_used': settings.RANKING_WEIGHTS,
                                    'computation_date': start_time.isoformat(),
                                    'data_period_days': score_data.get('data_period_days', 90),
                                }
                            }
                        )

                        action = 'Created' if created else 'Updated'
                        self.stdout.write(
                            f'{action} score for {farmer.user.get_full_name()}: '
                            f'{farmer_score.total_score:.2f}'
                        )
                        updated_count += 1

                    except Exception as e:
                        error_count += 1
                        logger.error(f'Error computing score for farmer {farmer.id}: {e}')
                        self.stdout.write(
                            self.style.ERROR(
                                f'Error processing {farmer.user.get_full_name()}: {e}'
                            )
                        )

                if options['dry_run']:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'DRY RUN completed. Would have processed {len(farmers)} farmers'
                        )
                    )
                    return

                # Update farmer rankings within each region
                self._update_regional_rankings(options['region'])

            end_time = timezone.now()
            duration = (end_time - start_time).total_seconds()

            self.stdout.write(
                self.style.SUCCESS(
                    f'Ranking recomputation completed in {duration:.2f} seconds\n'
                    f'Updated: {updated_count} farmers\n'
                    f'Errors: {error_count} farmers'
                )
            )

        except Exception as e:
            logger.error(f'Fatal error in ranking recomputation: {e}')
            raise CommandError(f'Ranking recomputation failed: {e}')

    def _update_regional_rankings(self, region_filter=None):
        """Update rank field based on total_score within each region"""
        from django.db.models import Window, F
        from django.db.models.functions import Rank
        
        self.stdout.write('Updating regional rankings...')

        # Get regions to process
        if region_filter:
            from regions.models import Region
            regions = Region.objects.filter(code=region_filter)
        else:
            # Get all regions that have farmers with scores
            regions = FarmerScore.objects.select_related('farmer__region')\
                .values('farmer__region')\
                .distinct()
            
            from regions.models import Region
            region_ids = [r['farmer__region'] for r in regions]
            regions = Region.objects.filter(id__in=region_ids)

        for region in regions:
            # Update rankings for this region using window function
            scores_in_region = FarmerScore.objects.filter(
                farmer__region=region
            ).annotate(
                new_rank=Window(
                    expression=Rank(),
                    order_by=F('total_score').desc()
                )
            )

            # Bulk update ranks
            updates = []
            for score in scores_in_region:
                score.rank = score.new_rank
                updates.append(score)

            if updates:
                FarmerScore.objects.bulk_update(updates, ['rank'])
                self.stdout.write(
                    f'Updated rankings for {len(updates)} farmers in {region.name}'
                )
