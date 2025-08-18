"""
Core views for the Kannammal Agro application.
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.contrib import messages
from django.db.models import Count, Avg, Sum
from django.utils import timezone
from datetime import timedelta

from farmers.models import Farmer
from pricing.models import FarmerPrice
from orders.models import Order
from ranking.models import FarmerScore
from .rbac import (
    admin_required, region_head_required, buyer_required, farmer_required
)


def home(request):
    """Home page with basic information"""
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    
    context = {
        'title': 'Welcome to Kannammal Agro',
    }
    return render(request, 'core/home_simple.html', context)


@login_required
def dashboard(request):
    """Role-based dashboard router"""
    user = request.user
    
    # Route to appropriate dashboard based on role
    if user.is_admin:
        return admin_dashboard(request)
    elif user.is_region_head:
        return region_head_dashboard(request)
    elif user.is_buyer_head:
        return buyer_head_dashboard(request)
    elif user.is_buyer:
        return buyer_dashboard(request)
    elif user.is_farmer:
        return farmer_dashboard(request)
    else:
        # Default dashboard for any other roles
        context = {'title': _('Dashboard'), 'user': user}
        return render(request, 'core/dashboard.html', context)


@admin_required
def admin_dashboard(request):
    """Admin dashboard with full system overview"""
    from accounts.models import User
    from catalog.models import SKU
    from regions.models import Region
    
    context = {
        'title': _('Admin Dashboard'),
        'user': request.user,
        'dashboard_type': 'admin'
    }
    
    # System-wide statistics
    context.update({
        'total_users': User.objects.count(),
        'total_farmers': Farmer.objects.count(),
        'total_regions': Region.objects.count(),
        'total_skus': SKU.objects.count(),
        'role_distribution': User.objects.values('role').annotate(count=Count('role')),
    })
    
    # Get comprehensive dashboard data
    context.update(_get_admin_dashboard_data(request.user))
    
    return render(request, 'core/dashboard_admin.html', context)


@region_head_required  
def region_head_dashboard(request):
    """Region head dashboard with region-specific data"""
    user_region = request.user.region
    
    context = {
        'title': _('Region Head Dashboard'),
        'user': request.user,
        'dashboard_type': 'region_head',
        'user_region': user_region
    }
    
    if not user_region:
        context['error'] = _('No region assigned to your account.')
        return render(request, 'core/dashboard_region_head.html', context)
    
    # Get region-specific data
    context.update(_get_region_dashboard_data(request.user))
    
    return render(request, 'core/dashboard_region_head.html', context)


@buyer_required
def buyer_head_dashboard(request):
    """Buyer head dashboard with buying operations overview"""
    context = {
        'title': _('Buyer Head Dashboard'),
        'user': request.user,
        'dashboard_type': 'buyer_head'
    }
    
    # Get buyer head specific data
    context.update(_get_buyer_head_dashboard_data(request.user))
    
    return render(request, 'core/dashboard_buyer_head.html', context)


@buyer_required
def buyer_dashboard(request):
    """Regular buyer dashboard"""
    context = {
        'title': _('Buyer Dashboard'),
        'user': request.user,
        'dashboard_type': 'buyer'
    }
    
    # Get buyer specific data
    context.update(_get_buyer_dashboard_data(request.user))
    
    return render(request, 'core/dashboard_buyer.html', context)


@farmer_required
def farmer_dashboard(request):
    """Farmer dashboard with their own data"""
    context = {
        'title': _('Farmer Dashboard'),
        'user': request.user,
        'dashboard_type': 'farmer'
    }
    
    # Get farmer specific data
    context.update(_get_farmer_dashboard_data(request.user))
    
    return render(request, 'core/dashboard_farmer.html', context)


def _get_admin_dashboard_data(user):
    """Get comprehensive dashboard data for admin users"""
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # Recent activity across all regions
    recent_prices = FarmerPrice.objects.select_related(
        'farmer__user', 'sku', 'region'
    ).order_by('-created_at')[:10]
    
    recent_orders = Order.objects.select_related(
        'farmer__user', 'assigned_buyer', 'sku'
    ).order_by('-created_at')[:10]
    
    # System performance metrics
    weekly_stats = {
        'new_farmers': Farmer.objects.filter(created_at__gte=week_ago).count(),
        'price_submissions': FarmerPrice.objects.filter(date__gte=week_ago).count(),
        'orders_placed': Order.objects.filter(created_at__gte=week_ago).count(),
        'revenue': Order.objects.filter(
            created_at__gte=week_ago,
            status='completed'
        ).aggregate(total=Sum('total_amount'))['total'] or 0
    }
    
    return {
        'recent_prices': recent_prices,
        'recent_orders': recent_orders,
        'weekly_stats': weekly_stats,
    }


def _get_region_dashboard_data(user):
    """Get dashboard data for region head users"""
    region = user.region
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    
    # Region-specific data
    region_farmers = Farmer.objects.filter(region=region)
    
    recent_prices = FarmerPrice.objects.filter(
        region=region,
        date__gte=week_ago
    ).select_related('farmer__user', 'sku').order_by('-created_at')[:10]
    
    recent_orders = Order.objects.filter(
        farmer__region=region
    ).select_related('farmer__user', 'assigned_buyer', 'sku').order_by('-created_at')[:5]
    
    # Region performance
    region_stats = {
        'total_farmers': region_farmers.count(),
        'active_farmers': recent_prices.values('farmer').distinct().count(),
        'weekly_orders': Order.objects.filter(
            farmer__region=region,
            created_at__gte=week_ago
        ).count(),
        'avg_price': recent_prices.aggregate(avg=Avg('price'))['avg'] or 0
    }
    
    return {
        'recent_prices': recent_prices,
        'recent_orders': recent_orders,
        'region_stats': region_stats,
    }


def _get_buyer_head_dashboard_data(user):
    """Get dashboard data for buyer head users"""
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    
    # Latest prices across all regions
    latest_prices = FarmerPrice.objects.select_related(
        'farmer__user', 'sku', 'region'
    ).order_by('sku', 'region', '-date').distinct('sku', 'region')[:20]
    
    # All recent orders (buyer head can see all)
    recent_orders = Order.objects.select_related(
        'farmer__user', 'buyer', 'sku'
    ).order_by('-created_at')[:10]
    
    # Procurement statistics
    procurement_stats = {
        'pending_orders': Order.objects.filter(status='pending').count(),
        'weekly_orders': Order.objects.filter(created_at__gte=week_ago).count(),
        'top_suppliers': Farmer.objects.annotate(
            order_count=Count('orders')
        ).order_by('-order_count')[:5]
    }
    
    return {
        'latest_prices': latest_prices,
        'recent_orders': recent_orders,
        'procurement_stats': procurement_stats,
    }


def _get_buyer_dashboard_data(user):
    """Get dashboard data for regular buyer users"""
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    
    # Latest prices (same as buyer head but might be filtered differently in future)
    latest_prices = FarmerPrice.objects.select_related(
        'farmer__user', 'sku', 'region'
    ).order_by('sku', 'region', '-date').distinct('sku', 'region')[:15]
    
    # Only orders created by this buyer
    my_orders = Order.objects.filter(
        buyer=user
    ).select_related('farmer__user', 'sku').order_by('-created_at')[:10]
    
    # Buyer-specific stats
    buyer_stats = {
        'my_orders': my_orders.count(),
        'pending_orders': my_orders.filter(status='pending').count(),
        'weekly_orders': my_orders.filter(created_at__gte=week_ago).count(),
        'total_spent': my_orders.filter(
            status='completed'
        ).aggregate(total=Sum('total_amount'))['total'] or 0
    }
    
    return {
        'latest_prices': latest_prices,
        'my_orders': my_orders,
        'buyer_stats': buyer_stats,
    }


def _get_farmer_dashboard_data(user):
    """Get dashboard data for farmer users"""
    try:
        farmer = user.farmer_profile
    except:
        return {'error': _('Farmer profile not found')}
    
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    
    # Recent prices submitted
    recent_prices = FarmerPrice.objects.filter(
        farmer=farmer,
        date__gte=week_ago
    ).select_related('sku').order_by('-date')[:5]
    
    # Recent orders
    recent_orders = Order.objects.filter(
        farmer=farmer
    ).select_related('assigned_buyer').order_by('-created_at')[:5]
    
    # Performance stats
    total_orders = Order.objects.filter(farmer=farmer).count()
    # Calculate average score from ranking data instead of non-existent quality_rating
    avg_rating = FarmerScore.objects.filter(farmer=farmer).aggregate(
        avg_score=Avg('total_score')
    )['avg_score'] or 0
    
    # Current ranking
    try:
        farmer_score = FarmerScore.objects.get(farmer=farmer)
        current_rank = farmer_score.rank
        total_score = farmer_score.total_score
    except FarmerScore.DoesNotExist:
        current_rank = None
        total_score = 0
    
    return {
        'farmer': farmer,
        'recent_prices': recent_prices,
        'recent_orders': recent_orders,
        'stats': {
            'total_orders': total_orders,
            'avg_rating': round(avg_rating, 1),
            'current_rank': current_rank,
            'total_score': round(total_score, 1),
        }
    }


def _get_buyer_dashboard_data(user):
    """Get dashboard data for buyer/admin users"""
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    
    # Filter by region for buyer_head, all regions for admin
    region_filter = {} if user.role == 'admin' else {'farmer__region': user.region}
    
    # Recent price submissions
    recent_prices = FarmerPrice.objects.filter(
        date__gte=week_ago,
        **region_filter
    ).select_related('farmer__user', 'sku').order_by('-created_at')[:10]
    
    # Orders pending attention
    pending_orders = Order.objects.filter(
        status='pending',
        **region_filter
    ).select_related('farmer__user').order_by('-created_at')[:5]
    
    # Top farmers by ranking
    top_farmers = FarmerScore.objects.filter(
        **region_filter
    ).select_related('farmer__user').order_by('rank')[:5]
    
    # Summary stats
    total_farmers = Farmer.objects.filter(**region_filter).count()
    active_farmers = FarmerPrice.objects.filter(
        date__gte=week_ago,
        **region_filter
    ).values('farmer').distinct().count()
    
    total_orders = Order.objects.filter(**region_filter).count()
    pending_orders_count = Order.objects.filter(
        status='pending',
        **region_filter
    ).count()
    
    return {
        'recent_prices': recent_prices,
        'pending_orders': pending_orders,
        'top_farmers': top_farmers,
        'stats': {
            'total_farmers': total_farmers,
            'active_farmers': active_farmers,
            'total_orders': total_orders,
            'pending_orders': pending_orders_count,
        }
    }


class CustomLoginView(auth_views.LoginView):
    """Custom login view with redirect logic"""
    template_name = 'registration/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        return reverse_lazy('core:dashboard')
    
    def form_valid(self, form):
        messages.success(self.request, _('Welcome back!'))
        return super().form_valid(form)


class CustomLogoutView(auth_views.LogoutView):
    """Custom logout view"""
    next_page = reverse_lazy('accounts:login')
    
    def dispatch(self, request, *args, **kwargs):
        messages.success(request, _('You have been logged out successfully.'))
        return super().dispatch(request, *args, **kwargs)
