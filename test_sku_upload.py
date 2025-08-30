#!/usr/bin/env python
"""
Quick test script for bulk SKU upload functionality
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append('/Users/jerish/Desktop/WorkSpace/RCT/Kannammal_Agro')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kannammal_agro.settings')
django.setup()

from catalog.models import SKU

def test_sku_creation():
    """Test creating a few SKUs"""
    test_skus = [
        "Apple Red Delicious",
        "Tomato Country", 
        "Banana Nendran",
        "Coconut"
    ]
    
    print("Testing SKU creation...")
    
    for sku_name in test_skus:
        # Check if SKU already exists
        existing = SKU.objects.filter(name=sku_name).first()
        if existing:
            print(f"✓ SKU '{sku_name}' already exists with code: {existing.code}")
        else:
            # Create new SKU
            from core.views import generate_sku_code, determine_category
            
            sku_code = generate_sku_code(sku_name)
            category = determine_category(sku_name)
            
            sku = SKU.objects.create(
                code=sku_code,
                name=sku_name,
                category=category,
                unit='kg',
                is_active=True
            )
            print(f"✓ Created SKU '{sku_name}' with code: {sku.code}, category: {sku.category}")
    
    print(f"\nTotal SKUs in database: {SKU.objects.count()}")
    
    # List all SKUs
    print("\nAll SKUs:")
    for sku in SKU.objects.all()[:10]:  # Show first 10
        print(f"  - {sku.code}: {sku.name} ({sku.category})")
    
    if SKU.objects.count() > 10:
        print(f"  ... and {SKU.objects.count() - 10} more")

if __name__ == "__main__":
    test_sku_creation()
