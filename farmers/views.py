"""
Views for farmer management functionality.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext as _
from django.db.models import Avg, Count, Sum, Q
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json

from .models import Farmer
from .forms import FarmerRegistrationForm, FarmerProfileForm
from accounts.decorators import role_required
from ranking.models import FarmerScore


@login_required
@role_required(['admin', 'buyer_head'])
def farmer_list(request):
    """List all farmers with filtering and search"""
    user = request.user
    
    # Base queryset with region filtering for buyer_head
    farmers_qs = Farmer.objects.select_related('user', 'region')
    if user.role == 'buyer_head':
        farmers_qs = farmers_qs.filter(region=user.region)
    
    # Search functionality
    search_query = request.GET.get('search', '').strip()
    if search_query:
        farmers_qs = farmers_qs.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(contact_number__icontains=search_query) |
            Q(farm_type__icontains=search_query)
        )
    
    # Filtering
    region_filter = request.GET.get('region')
    if region_filter and user.role == 'admin':
        farmers_qs = farmers_qs.filter(region__code=region_filter)
    
    status_filter = request.GET.get('status')
    if status_filter:
        if status_filter == 'active':
            farmers_qs = farmers_qs.filter(is_active=True)
        elif status_filter == 'inactive':
            farmers_qs = farmers_qs.filter(is_active=False)
        elif status_filter == 'verified':
            farmers_qs = farmers_qs.filter(is_verified=True)
        elif status_filter == 'unverified':
            farmers_qs = farmers_qs.filter(is_verified=False)
    
    # Ordering
    order_by = request.GET.get('order_by', '-created_at')
    if order_by in ['name', '-name', 'created_at', '-created_at', 'region', '-region']:
        if order_by.replace('-', '') == 'name':
            order_by = order_by.replace('name', 'user__first_name')
        farmers_qs = farmers_qs.order_by(order_by)
    
    # Pagination
    paginator = Paginator(farmers_qs, 25)
    page_number = request.GET.get('page')
    farmers = paginator.get_page(page_number)
    
    # Get regions for filter dropdown (admin only)
    regions = None
    if user.role == 'admin':
        from regions.models import Region
        regions = Region.objects.filter(is_active=True)
    
    context = {
        'title': _('Farmers'),
        'farmers': farmers,
        'search_query': search_query,
        'region_filter': region_filter,
        'status_filter': status_filter,
        'order_by': order_by,
        'regions': regions,
        'can_add_farmer': user.role in ['admin', 'buyer_head'],
    }
    
    return render(request, 'farmers/list.html', context)


@login_required
@role_required(['farmer'])
def my_profile(request):
    """Farmer's own profile view"""
    try:
        farmer = request.user.farmer_profile
    except:
        messages.error(request, _('Farmer profile not found.'))
        return redirect('core:dashboard')
    
    # Get performance data
    farmer_score = FarmerScore.objects.filter(farmer=farmer).first()
    
    # Recent activity summary
    recent_prices = farmer.prices.select_related('sku').order_by('-created_at')[:5]
    recent_orders = farmer.orders.select_related('buyer').order_by('-created_at')[:5]
    
    context = {
        'title': _('My Profile'),
        'farmer': farmer,
        'farmer_score': farmer_score,
        'recent_prices': recent_prices,
        'recent_orders': recent_orders,
    }
    
    return render(request, 'farmers/my_profile.html', context)
