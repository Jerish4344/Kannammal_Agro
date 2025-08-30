"""
Management command to seed the database with initial test data.
Creates regions, SKUs, farmers, and sample data for testing.
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
import random
from datetime import timedelta

from regions.models import Region
from catalog.models import SKU
from farmers.models import Farmer
from pricing.models import FarmerPrice
from orders.models import Order

User = get_user_model()

# Behavior patterns for farmers - simple mapping
FARMER_PATTERNS = {
    'raman.kumar': 'high_performer',
    'lakshmi.devi': 'high_performer',
    'suresh.patel': 'consistent',
    'meera.sharma': 'consistent',
    'vijay.singh': 'consistent',
    'prakash.reddy': 'unreliable_cheap',
    'kavitha.nair': 'unreliable_cheap',
    'arjun.krishnan': 'new_farmer',
}


class Command(BaseCommand):
    help = 'Seed database with initial test data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before seeding',
        )
        parser.add_argument(
            '--farmers-only',
            action='store_true',
            help='Only create farmer data, skip regions and SKUs',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Starting database seeding process')
        )

        with transaction.atomic():
            if options['clear']:
                self._clear_data()

            if not options['farmers_only']:
                self._create_regions()
                self._create_skus()
            
            self._create_users_and_farmers()
            self._create_sample_prices()
            self._create_sample_orders()

        self.stdout.write(
            self.style.SUCCESS('Database seeding completed successfully')
        )

    def _clear_data(self):
        """Clear existing test data"""
        self.stdout.write('Clearing existing data...')
        
        # Clear in dependency order
        Order.objects.all().delete()
        FarmerPrice.objects.all().delete()
        Farmer.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()
        SKU.objects.all().delete()
        Region.objects.all().delete()

    def _create_regions(self):
        """Create 3 test regions"""
        self.stdout.write('Creating regions...')
        
        regions_data = [
            {
                'name': 'Tamil Nadu',
                'code': 'TN',
                'description': 'Southern region covering Tamil Nadu state',
                'is_active': True,
            },
            {
                'name': 'Karnataka',
                'code': 'KA', 
                'description': 'Southern region covering Karnataka state',
                'is_active': True,
            },
            {
                'name': 'Andhra Pradesh',
                'code': 'AP',
                'description': 'Southern region covering Andhra Pradesh state',
                'is_active': True,
            }
        ]

        for region_data in regions_data:
            region, created = Region.objects.get_or_create(
                code=region_data['code'],
                defaults=region_data
            )
            action = 'Created' if created else 'Found existing'
            self.stdout.write(f'  {action}: {region.name}')

    def _create_skus(self):
        """Create 10 SKUs"""
        self.stdout.write('Creating SKUs...')

        # Create SKUs
        skus_data = [
            {'name': 'Tomato', 'code': 'TOM001', 'category': 'vegetable', 'unit': 'kg'},
            {'name': 'Onion', 'code': 'ONI001', 'category': 'vegetable', 'unit': 'kg'},
            {'name': 'Potato', 'code': 'POT001', 'category': 'vegetable', 'unit': 'kg'},
            {'name': 'Banana', 'code': 'BAN001', 'category': 'fruit', 'unit': 'dozen'},
            {'name': 'Apple', 'code': 'APP001', 'category': 'fruit', 'unit': 'kg'},
            {'name': 'Orange', 'code': 'ORA001', 'category': 'fruit', 'unit': 'kg'},
            {'name': 'Spinach', 'code': 'SPI001', 'category': 'vegetable', 'unit': 'kg'},
            {'name': 'Coriander', 'code': 'COR001', 'category': 'vegetable', 'unit': 'kg'},
            {'name': 'Green Chili', 'code': 'CHI001', 'category': 'vegetable', 'unit': 'kg'},
            {'name': 'Carrot', 'code': 'CAR001', 'category': 'vegetable', 'unit': 'kg'},
        ]

        for sku_data in skus_data:
            sku, created = SKU.objects.get_or_create(
                code=sku_data['code'],
                defaults={
                    'name': sku_data['name'],
                    'category': sku_data['category'],
                    'unit': sku_data['unit'],
                    'is_active': True,
                }
            )
            action = 'Created' if created else 'Found existing'
            self.stdout.write(f'  {action}: {sku.name} ({sku.unit})')

    def _create_users_and_farmers(self):
        """Create users and 8 farmers with different behavior patterns"""
        self.stdout.write('Creating users and farmers...')

        regions = list(Region.objects.all())
        if not regions:
            self.stdout.write(
                self.style.ERROR('No regions found. Run without --farmers-only first.')
            )
            return

        # Create admin user
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@kannammalagro.com',
                'first_name': 'Admin',
                'last_name': 'User',
                'role': 'admin',
                'is_staff': True,
                'is_superuser': True,
                'region': regions[0],
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write('  Created admin user: admin@kannammalagro.com')

        # Create buyer heads for each region
        for i, region in enumerate(regions):
            buyer_user, created = User.objects.get_or_create(
                username=f'buyer{i+1}',
                defaults={
                    'email': f'buyer{i+1}@kannammalagro.com',
                    'first_name': f'Buyer{i+1}',
                    'last_name': 'Head',
                    'role': 'buyer_head',
                    'region': region,
                }
            )
            if created:
                buyer_user.set_password('buyer123')
                buyer_user.save()
                self.stdout.write(f'  Created buyer head: {buyer_user.email}')

        # Create farmers with different behavior patterns
        farmers_data = [
            # High performers
            {'name': 'Raman Kumar', 'phone': '9876543210', 'region_idx': 0, 'pattern': 'high_performer'},
            {'name': 'Lakshmi Devi', 'phone': '9876543211', 'region_idx': 0, 'pattern': 'high_performer'},
            
            # Consistent mid-range
            {'name': 'Suresh Patel', 'phone': '9876543212', 'region_idx': 1, 'pattern': 'consistent'},
            {'name': 'Meera Sharma', 'phone': '9876543213', 'region_idx': 1, 'pattern': 'consistent'},
            {'name': 'Vijay Singh', 'phone': '9876543214', 'region_idx': 2, 'pattern': 'consistent'},
            
            # Unreliable but cheap
            {'name': 'Prakash Reddy', 'phone': '9876543215', 'region_idx': 2, 'pattern': 'unreliable_cheap'},
            {'name': 'Kavitha Nair', 'phone': '9876543216', 'region_idx': 0, 'pattern': 'unreliable_cheap'},
            
            # New farmer
            {'name': 'Arjun Krishnan', 'phone': '9876543217', 'region_idx': 1, 'pattern': 'new_farmer'},
        ]

        for farmer_data in farmers_data:
            region = regions[farmer_data['region_idx']]
            email = f"{farmer_data['name'].lower().replace(' ', '.')}@farmer.com"
            username = farmer_data['name'].lower().replace(' ', '.')
            
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': farmer_data['name'].split()[0],
                    'last_name': ' '.join(farmer_data['name'].split()[1:]),
                    'role': 'farmer',
                    'region': region,
                }
            )
            
            if created:
                user.set_password('farmer123')
                user.save()

                farmer, created = Farmer.objects.get_or_create(
                    user=user,
                    defaults={
                        'contact_number': farmer_data['phone'],
                        'region': region,
                        'farm_size': Decimal(str(random.uniform(1.0, 10.0))),
                        'farm_type': random.choice([
                            'Vegetable',
                            'Fruit', 
                            'Mixed',
                            'Organic'
                        ]),
                        'address': f'{farmer_data["name"]}, {region.name}',
                        'is_active': farmer_data['pattern'] != 'new_farmer',
                    }
                )
                self.stdout.write(f'  Created farmer: {farmer_data["name"]} ({region.code})')

    def _create_sample_prices(self):
        """Create sample price submissions with different patterns"""
        self.stdout.write('Creating sample price data...')

        farmers = Farmer.objects.all()
        skus = SKU.objects.all()
        
        if not farmers or not skus:
            self.stdout.write('No farmers or SKUs found, skipping price creation')
            return

        # Create prices for last 30 days
        for day_offset in range(30):
            date = timezone.now().date() - timedelta(days=day_offset)
            
            for farmer in farmers:
                # Each farmer submits 2-4 SKUs per day randomly
                farmer_skus = random.sample(list(skus), random.randint(2, 4))
                
                for sku in farmer_skus:
                    # Skip some days for unreliable farmers
                    pattern = FARMER_PATTERNS.get(farmer.user.username, 'consistent')
                    if pattern == 'unreliable_cheap' and random.random() < 0.4:
                        continue
                    
                    # Skip recent days for new farmers
                    if pattern == 'new_farmer' and day_offset > 5:
                        continue

                    price = self._generate_price_for_farmer_pattern(farmer, sku)
                    quality_rating = self._generate_quality_for_farmer_pattern(farmer)
                    
                    FarmerPrice.objects.get_or_create(
                        farmer=farmer,
                        sku=sku,
                        date=date,
                        defaults={
                            'price': price,
                            'quantity_available': Decimal(str(random.uniform(10.0, 500.0))),
                            'region': farmer.region,
                            'submitted_via': random.choice(['voice', 'text']),
                            'notes': f'Sample price data for {sku.name}',
                        }
                    )

        self.stdout.write(f'  Created price data for {farmers.count()} farmers')

    def _generate_price_for_farmer_pattern(self, farmer, sku):
        """Generate price based on farmer behavior pattern"""
        # For now, generate simple random prices since SKU doesn't have min/max price
        base_price = Decimal('50.00')  # Default base price
        pattern = FARMER_PATTERNS.get(farmer.user.username, 'consistent')
        
        if pattern == 'high_performer':
            # Competitive but fair prices
            return Decimal(str(float(base_price) * random.uniform(0.9, 1.1)))
        elif pattern == 'consistent':
            # Consistent mid-range prices
            return Decimal(str(float(base_price) * random.uniform(0.95, 1.05)))
        elif pattern == 'unreliable_cheap':
            # Very low prices but unreliable
            return Decimal(str(float(base_price) * random.uniform(0.7, 0.9)))
        else:  # new_farmer
            # Higher prices due to inexperience
            return Decimal(str(float(base_price) * random.uniform(1.1, 1.3)))

    def _generate_quality_for_farmer_pattern(self, farmer):
        """Generate quality rating based on farmer pattern"""
        pattern = FARMER_PATTERNS.get(farmer.user.username, 'consistent')
        if pattern == 'high_performer':
            return random.uniform(4.0, 5.0)
        elif pattern == 'consistent':
            return random.uniform(3.5, 4.5)
        elif pattern == 'unreliable_cheap':
            return random.uniform(2.0, 3.5)
        else:  # new_farmer
            return random.uniform(3.0, 4.0)

    def _create_sample_orders(self):
        """Create sample orders"""
        self.stdout.write('Creating sample orders...')

        buyer_heads = User.objects.filter(role='buyer_head')
        farmers = list(Farmer.objects.all())
        skus = list(SKU.objects.all())

        if not buyer_heads or not farmers or not skus:
            return

        # Create 20 sample orders over last 15 days
        for _ in range(20):
            buyer_heads = [u for u in User.objects.filter(role='procurement_head')]
            buyer = random.choice(buyer_heads) if buyer_heads else None
            farmer = random.choice(farmers)
            sku = random.choice(skus)
            quantity = Decimal(str(random.uniform(10.0, 100.0)))
            unit_price = self._generate_price_for_farmer_pattern(farmer, sku)
            total_amount = quantity * unit_price

            if buyer:
                order = Order.objects.create(
                    order_number=f'ORD{random.randint(1000, 9999)}',
                    sku=sku,
                    farmer=farmer,
                    region=farmer.region,
                    quantity=quantity,
                    unit_price=unit_price,
                    total_amount=total_amount,
                    ordered_by=buyer,
                    status=random.choice(['pending', 'confirmed', 'delivered', 'cancelled']),
                )

        self.stdout.write(f'  Created {Order.objects.count()} sample orders')
