from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg, Sum, F
from farmers.models import Farmer
from pricing.models import FarmerPrice
from regions.models import Region

# Create your views here.

@login_required 
def dashboard(request):
    """Procurement dashboard with sourcing analytics - role-based access"""
    user = request.user
    print(f"=== DASHBOARD DEBUG: User {user.username} ===")
    
    if hasattr(user, 'farmer_profile'):
        # Farmer view - only their own data
        farmer = user.farmer_profile
        print(f"Farmer view for: {farmer}")
        
        # Get dashboard statistics - only for this farmer
        total_farmers = 1  # Just this farmer
        total_prices = FarmerPrice.objects.filter(farmer=farmer).count()
        total_regions = 1  # Just farmer's region
        
        # Calculate procurement metrics for this farmer only
        farmer_prices = FarmerPrice.objects.filter(farmer=farmer)
        avg_price = farmer_prices.aggregate(avg_price=Avg('price'))['avg_price'] or 0
        
        # Calculate total procurement value for this farmer
        total_procurement_value = farmer_prices.aggregate(
            total_value=Sum(F('price') * F('quantity_available'))
        )['total_value'] or 0
        
        # Calculate total quantity sourced by this farmer
        total_quantity = farmer_prices.aggregate(
            total_qty=Sum('quantity_available')
        )['total_qty'] or 0
        
        # Get recent price submissions (last 10) - only this farmer's
        recent_prices = list(farmer_prices.select_related('sku', 'farmer__region').order_by('-submitted_at')[:10])
        
        print(f"Farmer view - recent prices count: {len(recent_prices)}")
        for price in recent_prices:
            print(f"  - ID {price.id}: {price.farmer} - {price.sku.name} - ₹{price.price}")
        
        context = {
            'total_farmers': total_farmers,
            'total_prices': total_prices,
            'total_regions': total_regions,
            'average_price': avg_price,
            'total_procurement_value': total_procurement_value,
            'total_quantity': total_quantity,
            'recent_prices': recent_prices,
            'is_farmer_view': True,
            'current_farmer': farmer,
        }
    else:
        # Admin/Management view - all data
        print(f"Admin/Buyer view for: {user.username}")
        
        # Get dashboard statistics
        total_farmers = Farmer.objects.count()
        total_prices = FarmerPrice.objects.count()
        total_regions = Region.objects.count()
        
        print(f"Total farmers: {total_farmers}, Total prices: {total_prices}")
        
        # Calculate procurement metrics
        avg_price = FarmerPrice.objects.aggregate(avg_price=Avg('price'))['avg_price'] or 0
        
        # Calculate total procurement value (price * quantity)
        total_procurement_value = FarmerPrice.objects.aggregate(
            total_value=Sum(F('price') * F('quantity_available'))
        )['total_value'] or 0
        
        # Calculate total quantity sourced
        total_quantity = FarmerPrice.objects.aggregate(
            total_qty=Sum('quantity_available')
        )['total_qty'] or 0
        
        # Get recent price submissions (last 10) - Force fresh query
        from django.db import connection
        print(f"Database connection: {connection.vendor}")
        
        recent_prices_query = FarmerPrice.objects.select_related('farmer__user', 'sku', 'region').order_by('-submitted_at')
        print(f"Query SQL: {recent_prices_query.query}")
        
        recent_prices = list(recent_prices_query[:10])
        
        print(f"Admin view - recent prices count: {len(recent_prices)}")
        for i, price in enumerate(recent_prices, 1):
            farmer_name = price.farmer.user.get_full_name() or price.farmer.user.username
            print(f"  {i}. ID {price.id}: Farmer {price.farmer.id} ({farmer_name}) - {price.sku.name} - ₹{price.price} - Date: {price.date}")
        
        context = {
            'total_farmers': total_farmers,
            'total_prices': total_prices,
            'total_regions': total_regions,
            'average_price': avg_price,
            'total_procurement_value': total_procurement_value,
            'total_quantity': total_quantity,
            'recent_prices': recent_prices,
            'is_farmer_view': False,
        }
    
    print(f"=== END DASHBOARD DEBUG ===")
    return render(request, 'reports/dashboard.html', context)

@login_required
def sales_report(request):
    """Procurement report (renamed from sales for clarity)"""
    # Since you're buying from farmers, this would be a procurement report
    return render(request, 'reports/sales.html', {})

@login_required
def farmer_report(request):
    """Farmer performance and pricing report - role-based access"""
    user = request.user
    
    # Check if user is a farmer
    if hasattr(user, 'farmer_profile'):
        # Farmers can only see their own data
        farmer = user.farmer_profile
        farmers = Farmer.objects.filter(id=farmer.id).annotate(
            price_count=Count('farmer_prices'),
            avg_price=Avg('farmer_prices__price')
        ).select_related('region')
        
        # Get only this farmer's price submissions
        recent_prices = FarmerPrice.objects.filter(farmer=farmer).select_related('sku').order_by('-submitted_at')[:10]
        
        context = {
            'farmers': farmers,
            'recent_prices': recent_prices,
            'is_farmer_view': True,
            'current_farmer': farmer,
        }
    else:
        # Admin, region heads, buyer heads can see all farmers
        farmers = Farmer.objects.annotate(
            price_count=Count('farmer_prices'),
            avg_price=Avg('farmer_prices__price')
        ).select_related('region').order_by('-price_count')
        
        context = {
            'farmers': farmers,
            'is_farmer_view': False,
        }
    
    return render(request, 'reports/farmer.html', context)

@login_required
def export_report(request):
    """Export report functionality"""
    return render(request, 'reports/export.html', {})
