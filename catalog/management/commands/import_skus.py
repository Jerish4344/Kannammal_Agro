"""Management command to import SKUs from a predefined list."""

from django.core.management.base import BaseCommand
from django.db import transaction
from catalog.models import SKU
import re


class Command(BaseCommand):
    help = 'Import SKUs from predefined list'
    
    SKU_LIST = [
        "Coconut",
        "Onion Big",
        "Tomato Country",
        "Carrot",
        "Pomegranate",
        "Potato",
        "Onion Sambar",
        "Tomato Hybrid",
        "Banana Nendran",
        "Beetroot",
        "Guava Thailand",
        "Apple Envy",
        "Cucumber Salad",
        "Apple Himachal Indian",
        "Ginger Fresh",
        "Apple Royal Gala",
        "Lemon",
        "Mango Neelam",
        "Orange Imported",
        "Beans French",
        "Ladies Finger",
        "Cauliflower",
        "Water Melon Kiran",
        "Chilli Green",
        "Garlic Himachal",
        "Banana Green Nendran",
        "Apple Red Delicious",
        "Cucumber Malabar",
        "Garlic Small",
        "American Sweet Corn Pack Of 2",
        "Dragon Fruit Red Indian Kg",
        "Pine Apple",
        "Apple Pink Lady",
        "Strawberry",
        "Garlic Big",
        "Mini Orange",
        "Gooseberry amla",
        "Cabbage",
        "Drum Stick",
        "Corriander Leaves",
        "Capsicum Green",
        "Brinjal Vari",
        "Kiwi Pack Of 3",
        "Coccinia",
        "Apple Granny Smith",
        "Papaya",
        "Chilli Thondan",
        "Banana Raw",
        "Chilli Bullet",
        "Apple Fuji",
        "Mango Raw",
        "Avacado Imported",
        "Sweet Potato",
        "Button Mushroom",
        "Dragon Fruit White",
        "American Sweet Corn Pc",
        "Snake Gourd",
        "Cucumber English",
        "Pear Red",
        "Banana Yellaki Rasakathali",
        "Blue Berry Imported",
        "Plums Indain",
        "Avacado",
        "Apple New Zealand Royal Gala",
        "Grapes Imported",
        "Beans Cowpea Long",
        "Bitter Gourd White",
        "Mango Raw Totapuri",
        "Pumpkin",
        "Pears Indian",
        "Beans Haricot",
        "Apple Shimla Indian",
        "Pomegranate Medium Kg",
        "Apple Washington Red",
        "Spinach Palak Bunch",
        "Bottle Gourd",
        "Yam",
        "Musk Melon",
        "Beans Cluster",
        "Rambutan",
        "Plums Imported",
        "Mint Leaves",
        "Colacasia Big",
        "Grapes Red Globe Indian",
        "Guava White",
        "Sweet Orange",
        "Bitter Gourd Green",
        "Tapioca",
        "Banana Red Kappa",
        "Grapes Dilkush",
        "Cucumber Madras",
        "Beans Avarai Small",
        "Broccoli",
        "Grapes Panner",
        "Banana Robusta Green",
        "Oyster Mushroom",
        "Koorka",
        "Grapes Banglore Blue",
        "Chilli bhajji",
        "Banana Karpooravalli",
        "Banana Robusta Yellow",
        "Brinjal Long Green",
        "Banana Poovan",
        "Brinjal Nadan",
        "Curry Leaves",
        "Banana Palayamthodan",
        "Amaranthus Green Bunch",
        "Ash Gourd",
        "Apple Goru",
        "Ground Nut",
        "Chow Chow",
        "Ridge Gourd",
        "Radish White",
        "Pear Green",
        "White Egg 6PC",
        "Beans Cowpea Small",
        "Water apple",
        "Colacasia Small",
        "Custard Apple",
        "Lettuce Ice Berg",
        "Amaranthus Red Bunch",
        "Chinese Cabbage",
        "Apple I Red",
        "Golden Kiwi 3Pc",
        "Apple Granny 4 Pcs",
        "Sapota  Cricket Ball",
        "Cabbage Red",
        "Sapota Hybrid",
        "Country Egg 6PC",
        "Mangosteen",
        "Capsicum Color",
        "Banana Flower",
        "Orange Nagpur",
        "Apple Granny 2 Pcs",
        "Apple Royal Gala 2 Pcs",
        "Snake Gourd Long",
        "Pumpkin Red",
        "Orange Mandarin 500gm",
        "Agathi Keera Bunch",
        "Grapes green imported",
        "Mango Totapuri",
        "Milky Mushroom",
        "Brinjal White",
        "Sambar Kit",
        "Baby Potato",
        "Apple Royal Gala 4 Pcs",
        "Jujube Fruit",
        "Veg Biryani Pack 250g",
        "Apple Pink lady 4 Pcs",
        "Spring Onion",
        "Plums imported 4 Pcs",
        "Zucchini Green",
        "Ponnanganni Keerai Bunch",
        "Baby Corn Unpleed",
        "Banana Leaves pc",
        "Sweet tamarind",
        "Zucchini Yellow",
        "Fresh Mango Juice 250ml",
        "Dragon Fruit Red",
        "Cut Fruit Mix",
        "Grapes Sonaka Seedless",
        "Tn Beetroot",
        "Dragon Fruit Yelllow Kg",
        "Mango Sindhura",
        "Spring Onion Pc",
        "Celery",
        "Grapes Balck Seedless",
        "Leek",
        "Fresh fig",
        "Litchi",
        "Sour passion fruit Kg",
        "Lemon Big",
        "Mango Imam",
        "KARUNAI KILANGU",
        "Knolkhol Kg",
        "Bitter Gourd Nadan",
        "Coriander Kg",
        "Mango Dasheri",
        "Marigold Flower",
        "Pineapple Small",
        "Water Melon",
        "Fresh pigeon pea Kg",
        "Apple Kashmir Red Delicious",
        "Basil Leaves",
        "Fried Rice Mix 300g",
        "Baby Corn Peeled",
        "Lettuce Head Bunch-Kg",
        "Rosemary",
        "American Sweetcorn Peeled-Unit",
        "Micro Radish",
        "Sun Melon",
        "Tn Cabbage",
        "Tender Jack Fruit"
    ]

    def generate_sku_code(self, name):
        """Generate a unique SKU code from product name."""
        # Remove special characters and convert to uppercase
        code = re.sub(r'[^a-zA-Z0-9\s]', '', name)
        # Take first 3 characters of each word, max 10 chars total
        words = code.split()
        if len(words) == 1:
            return words[0][:10].upper()
        elif len(words) == 2:
            return (words[0][:4] + words[1][:4]).upper()
        else:
            return ''.join([word[:3] for word in words[:3]]).upper()

    def categorize_product(self, name):
        """Categorize product based on name keywords."""
        name_lower = name.lower()
        
        # Fruits
        fruit_keywords = [
            'apple', 'banana', 'mango', 'orange', 'grapes', 'strawberry', 
            'pineapple', 'papaya', 'guava', 'lemon', 'kiwi', 'dragon fruit',
            'pomegranate', 'avacado', 'pear', 'plums', 'litchi', 'rambutan',
            'mangosteen', 'custard apple', 'sapota', 'gooseberry', 'amla',
            'blue berry', 'fresh fig', 'water melon', 'musk melon', 'sun melon',
            'sweet tamarind', 'jujube fruit', 'water apple', 'passion fruit'
        ]
        
        # Vegetables  
        vegetable_keywords = [
            'onion', 'tomato', 'carrot', 'potato', 'beetroot', 'cucumber',
            'ginger', 'beans', 'ladies finger', 'cauliflower', 'chilli',
            'garlic', 'capsicum', 'brinjal', 'cabbage', 'drum stick',
            'coccinia', 'gourd', 'spinach', 'yam', 'broccoli', 'mushroom',
            'radish', 'lettuce', 'amaranthus', 'chow chow', 'ridge gourd',
            'ash gourd', 'colacasia', 'tapioca', 'koorka', 'celery', 'leek',
            'zucchini', 'corn', 'pumpkin'
        ]
        
        # Check for fruits
        for keyword in fruit_keywords:
            if keyword in name_lower:
                return 'fruit'
        
        # Check for vegetables
        for keyword in vegetable_keywords:
            if keyword in name_lower:
                return 'vegetable'
        
        # Special cases
        if any(word in name_lower for word in ['leaves', 'flower', 'bunch']):
            return 'vegetable'
        elif any(word in name_lower for word in ['egg', 'kit', 'mix', 'juice']):
            return 'other'
        elif 'coconut' in name_lower:
            return 'fruit'
        
        return 'vegetable'  # Default

    def determine_unit(self, name):
        """Determine unit based on product name."""
        name_lower = name.lower()
        
        if any(word in name_lower for word in ['pack', 'pc', 'pcs', 'piece']):
            return 'piece'
        elif any(word in name_lower for word in ['bunch', 'leaves']):
            return 'bundle'
        elif 'kg' in name_lower:
            return 'kg'
        elif any(word in name_lower for word in ['ml', 'gm', 'gram']):
            return 'gram'
        else:
            return 'kg'  # Default

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be imported without actually creating records',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No records will be created')
            )
        
        created_count = 0
        updated_count = 0
        error_count = 0
        
        for product_name in self.SKU_LIST:
            try:
                # Generate SKU code
                sku_code = self.generate_sku_code(product_name)
                
                # Ensure uniqueness
                base_code = sku_code
                counter = 1
                while SKU.objects.filter(code=sku_code).exists():
                    sku_code = f"{base_code}{counter:02d}"
                    counter += 1
                
                # Determine category and unit
                category = self.categorize_product(product_name)
                unit = self.determine_unit(product_name)
                
                if not dry_run:
                    sku, created = SKU.objects.get_or_create(
                        name=product_name,
                        defaults={
                            'code': sku_code,
                            'category': category,
                            'unit': unit,
                            'is_active': True,
                            'min_order_quantity': 1.0
                        }
                    )
                    
                    if created:
                        created_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'Created: {sku.code} - {sku.name} '
                                f'({sku.category}, {sku.unit})'
                            )
                        )
                    else:
                        updated_count += 1
                        self.stdout.write(
                            self.style.WARNING(
                                f'Already exists: {sku.code} - {sku.name}'
                            )
                        )
                else:
                    self.stdout.write(
                        f'Would create: {sku_code} - {product_name} '
                        f'({category}, {unit})'
                    )
                    created_count += 1
                    
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(
                        f'Error processing {product_name}: {str(e)}'
                    )
                )
        
        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f'\n=== IMPORT SUMMARY ===\n'
                f'Created: {created_count}\n'
                f'Already existed: {updated_count}\n'
                f'Errors: {error_count}\n'
                f'Total processed: {len(self.SKU_LIST)}'
            )
        )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    '\nThis was a dry run. Use the command without --dry-run to actually import the data.'
                )
            )
