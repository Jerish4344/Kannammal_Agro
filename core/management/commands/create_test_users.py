"""Management command to create test users with different roles."""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from farmers.models import Farmer
from regions.models import Region
import random

User = get_user_model()


class Command(BaseCommand):
    help = 'Create test users with different roles for testing role-based access'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Delete existing test users before creating new ones',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options['reset']:
            # Delete existing test users (except superuser)
            User.objects.filter(username__startswith='test_').delete()
            self.stdout.write(self.style.WARNING('Deleted existing test users'))

        # Ensure we have at least one region
        region, created = Region.objects.get_or_create(
            name='Tamil Nadu',
            defaults={
                'code': 'TN',
                'state': 'Tamil Nadu',
                'is_active': True
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created region: {region.name}'))

        # Test users to create
        test_users = [
            {
                'username': 'test_admin',
                'email': 'admin@kannammalagro.com',
                'first_name': 'Admin',
                'last_name': 'User',
                'role': 'admin',
                'password': 'test123'
            },
            {
                'username': 'test_region_head',
                'email': 'regionhead@kannammalagro.com',
                'first_name': 'Region',
                'last_name': 'Head',
                'role': 'region_head',
                'password': 'test123',
                'region': region
            },
            {
                'username': 'test_buyer_head',
                'email': 'buyerhead@kannammalagro.com',
                'first_name': 'Buyer',
                'last_name': 'Head',
                'role': 'buyer_head',
                'password': 'test123'
            },
            {
                'username': 'test_buyer',
                'email': 'buyer@kannammalagro.com',
                'first_name': 'Regular',
                'last_name': 'Buyer',
                'role': 'buyer',
                'password': 'test123'
            },
            {
                'username': 'test_farmer',
                'email': 'farmer@kannammalagro.com',
                'first_name': 'Test',
                'last_name': 'Farmer',
                'role': 'farmer',
                'password': 'test123',
                'region': region
            }
        ]

        created_count = 0
        
        for user_data in test_users:
            username = user_data['username']
            
            # Check if user already exists
            if User.objects.filter(username=username).exists():
                self.stdout.write(
                    self.style.WARNING(f'User {username} already exists, skipping...')
                )
                continue

            # Extract region and password
            region_obj = user_data.pop('region', None)
            password = user_data.pop('password')
            
            # Create user
            user = User.objects.create_user(
                password=password,
                **user_data
            )
            
            # Set region if specified
            if region_obj:
                user.region = region_obj
                user.save()
            
            # Create farmer profile if user is farmer
            if user.role == 'farmer':
                farmer, farmer_created = Farmer.objects.get_or_create(
                    user=user,
                    defaults={
                        'region': region_obj,
                        'contact_number': '+91-9876543210',
                        'address': '123 Test Village, Test District',
                        'is_active': True
                    }
                )
                if farmer_created:
                    self.stdout.write(
                        self.style.SUCCESS(f'Created farmer profile for {username}')
                    )
            
            created_count += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f'Created user: {username} ({user.get_role_display()}) - Password: {password}'
                )
            )

        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f'\n=== SUMMARY ===\n'
                f'Created {created_count} test users\n'
                f'Login credentials (username / password):\n'
                f'- test_admin / test123 (Admin)\n'
                f'- test_region_head / test123 (Region Head)\n'
                f'- test_buyer_head / test123 (Buyer Head)\n'
                f'- test_buyer / test123 (Buyer)\n'
                f'- test_farmer / test123 (Farmer)\n'
            )
        )
