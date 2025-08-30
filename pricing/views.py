"""
Views for price submission and comparison functionality.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext as _
from django.db.models import Min, Avg, Q, Count
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from datetime import timedelta
import csv

from .models import FarmerPrice
from .forms import PriceSubmissionForm
from catalog.models import SKU
from farmers.models import Farmer
from accounts.decorators import role_required


@login_required
@role_required(['farmer'])
def submit_price(request):
    """Farmer submits prices for their products"""
    try:
        farmer = request.user.farmer_profile
    except:
        messages.error(request, _('Farmer profile not found.'))
        return redirect('core:dashboard')
    
    if request.method == 'POST':
        form = PriceSubmissionForm(request.POST, farmer=farmer)
        if form.is_valid():
            farmer_price = form.save(commit=False)
            farmer_price.farmer = farmer
            farmer_price.region = farmer.region  # Set region from farmer's region
            farmer_price.save()
            
            messages.success(
                request,
                _('🎉 You have successfully submitted your price for {}! Thank you for your submission.').format(farmer_price.sku.name)
            )
            return redirect('pricing:submit_price')
    else:
        form = PriceSubmissionForm(farmer=farmer)
    
    # Get today's submitted prices
    today_prices = FarmerPrice.objects.filter(
        farmer=farmer,
        date=timezone.now().date()
    ).select_related('sku')
    
    # Get market stats for sidebar
    today = timezone.now().date()
    market_stats = {
        'active_farmers': Farmer.objects.filter(is_active=True).count(),
        'today_submissions': FarmerPrice.objects.filter(date=today).count(),
        'available_skus': SKU.objects.filter(is_active=True).count(),
    }
    
    context = {
        'title': _('Submit Prices'),
        'form': form,
        'today_prices': today_prices,
        'farmer': farmer,
        'today': today,
        'market_stats': market_stats,
    }
    
    return render(request, 'pricing/submit_price.html', context)


@login_required
@role_required(['buyer_head', 'admin'])
def price_comparison(request):
    """Compare prices from different farmers"""
    user = request.user
    
    # Get filter parameters
    sku_id = request.GET.get('sku')
    date_filter = request.GET.get('date', 'today')
    region_filter = request.GET.get('region')
    
    # Determine date range
    today = timezone.now().date()
    if date_filter == 'today':
        date_from = today
        date_to = today
    elif date_filter == 'week':
        date_from = today - timedelta(days=7)
        date_to = today
    elif date_filter == 'month':
        date_from = today - timedelta(days=30)
        date_to = today
    else:
        date_from = today
        date_to = today
    
    # Base queryset with date filtering
    prices_qs = FarmerPrice.objects.filter(
        date__gte=date_from,
        date__lte=date_to
    ).select_related('farmer__user', 'farmer__region', 'sku')
    
    # Region filtering for buyer_head
    if user.role == 'buyer_head':
        prices_qs = prices_qs.filter(farmer__region=user.region)
    elif region_filter:
        prices_qs = prices_qs.filter(farmer__region__code=region_filter)
    
    # SKU filtering
    if sku_id:
        prices_qs = prices_qs.filter(sku_id=sku_id)
    
    # Order by SKU, then by price
    prices_qs = prices_qs.order_by('sku__name', 'price', '-submitted_at')
    
    # Get available SKUs for dropdown
    available_skus = SKU.objects.filter(is_active=True).order_by('name')
    
    # Get regions for admin users
    regions = None
    if user.role == 'admin':
        from regions.models import Region
        regions = Region.objects.filter(is_active=True)
    
    # Group prices by SKU for better display
    prices_by_sku = {}
    for price in prices_qs:
        if price.sku.name not in prices_by_sku:
            prices_by_sku[price.sku.name] = []
        prices_by_sku[price.sku.name].append(price)
    
    # Calculate price rankings for color coding
    for sku_name, price_list in prices_by_sku.items():
        if len(price_list) >= 2:
            # Sort by price and assign ranks
            sorted_prices = sorted(price_list, key=lambda p: p.price)
            for i, price in enumerate(sorted_prices):
                if i == 0:
                    price.price_rank = 'lowest'  # Green
                elif i == 1 and len(sorted_prices) > 2:
                    price.price_rank = 'second'  # Yellow
                else:
                    price.price_rank = 'higher'  # Red
        else:
            # Single price, mark as neutral
            for price in price_list:
                price.price_rank = 'neutral'
    
    context = {
        'title': _('Price Comparison'),
        'prices_by_sku': prices_by_sku,
        'available_skus': available_skus,
        'regions': regions,
        'filters': {
            'sku_id': sku_id,
            'date_filter': date_filter,
            'region_filter': region_filter,
        },
        'date_from': date_from,
        'date_to': date_to,
    }
    
    return render(request, 'pricing/comparison.html', context)


@login_required
@role_required(['buyer_head', 'admin'])
def export_prices(request):
    """Export price data to CSV"""
    user = request.user
    
    # Get filter parameters (same as price_comparison)
    sku_id = request.GET.get('sku')
    date_filter = request.GET.get('date', 'today')
    region_filter = request.GET.get('region')
    
    # Determine date range
    today = timezone.now().date()
    if date_filter == 'today':
        date_from = today
        date_to = today
    elif date_filter == 'week':
        date_from = today - timedelta(days=7)
        date_to = today
    elif date_filter == 'month':
        date_from = today - timedelta(days=30)
        date_to = today
    else:
        date_from = today
        date_to = today
    
    # Build queryset (same logic as price_comparison)
    prices_qs = FarmerPrice.objects.filter(
        date__gte=date_from,
        date__lte=date_to
    ).select_related('farmer__user', 'farmer__region', 'sku')
    
    if user.role == 'buyer_head':
        prices_qs = prices_qs.filter(farmer__region=user.region)
    elif region_filter:
        prices_qs = prices_qs.filter(farmer__region__code=region_filter)
    
    if sku_id:
        prices_qs = prices_qs.filter(sku_id=sku_id)
    
    prices_qs = prices_qs.order_by('sku__name', 'price')
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="prices_{date_from}_{date_to}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Date', 'SKU', 'Farmer Name', 'Region', 'Price per Unit', 
        'Available Quantity', 'Submission Method', 'Notes'
    ])
    
    for price in prices_qs:
        writer.writerow([
            price.date,
            price.sku.name,
            price.farmer.user.get_full_name(),
            price.farmer.region.name,
            price.price,
            price.quantity_available,
            price.submitted_via,
            price.notes,
        ])
    
    return response


@login_required
@role_required(['farmer'])
def my_price_history(request):
    """Farmer views their price submission history"""
    try:
        farmer = request.user.farmer_profile
    except:
        messages.error(request, _('Farmer profile not found.'))
        return redirect('core:dashboard')
    
    # Get filter parameters
    sku_filter = request.GET.get('sku')
    days_filter = int(request.GET.get('days', 30))
    
    # Build queryset
    prices_qs = FarmerPrice.objects.filter(farmer=farmer).select_related('sku')
    
    if sku_filter:
        prices_qs = prices_qs.filter(sku_id=sku_filter)
    
    if days_filter:
        cutoff_date = timezone.now().date() - timedelta(days=days_filter)
        prices_qs = prices_qs.filter(date__gte=cutoff_date)
    
    prices_qs = prices_qs.order_by('-date', 'sku__name')
    
    # Get available SKUs for farmer
    farmer_skus = SKU.objects.filter(
        farmerprices__farmer=farmer
    ).distinct().order_by('name')
    
    # Calculate some statistics
    stats = prices_qs.aggregate(
        avg_price=Avg('price'),
        total_submissions=Count('id'),
        avg_quantity=Avg('quantity_available'),
    )
    
    context = {
        'title': _('My Price History'),
        'prices': prices_qs,
        'farmer_skus': farmer_skus,
        'stats': stats,
        'filters': {
            'sku_filter': sku_filter,
            'days_filter': days_filter,
        },
    }
    
    return render(request, 'pricing/my_history.html', context)


@login_required
@require_http_methods(['GET'])
def api_sku_info(request, sku_id):
    """API endpoint to get SKU information for price submission"""
    try:
        sku = SKU.objects.get(id=sku_id, is_active=True)
        
        # Get recent market data
        recent_prices = FarmerPrice.objects.filter(
            sku=sku,
            date__gte=timezone.now().date() - timedelta(days=7)
        ).aggregate(
            min_price=Min('price'),
            avg_price=Avg('price'),
        )
        
        data = {
            'id': sku.id,
            'name': sku.name,
            'unit': sku.unit,
            'recent_min_price': float(recent_prices['min_price']) if recent_prices['min_price'] else None,
            'recent_avg_price': float(recent_prices['avg_price']) if recent_prices['avg_price'] else None,
        }
        
        return JsonResponse(data)
    
    except SKU.DoesNotExist:
        return JsonResponse({'error': 'SKU not found'}, status=404)
