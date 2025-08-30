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
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
import csv
import io
import re

from farmers.models import Farmer
from pricing.models import FarmerPrice
from orders.models import Order
from ranking.models import FarmerScore
from catalog.models import SKU
from .rbac import (
    admin_required, region_head_required, buyer_required, farmer_required
)


def home(request):
    """Redirect to dashboard if authenticated, otherwise to login"""
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    else:
        return redirect('accounts:login')


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
    
    # Latest prices across all regions (MySQL-compatible approach)
    # Get latest price per SKU-region combination
    latest_prices = []
    sku_region_combinations = FarmerPrice.objects.values('sku', 'region').distinct()
    
    for combo in sku_region_combinations[:20]:
        latest_price = FarmerPrice.objects.filter(
            sku=combo['sku'], 
            region=combo['region']
        ).select_related('farmer__user', 'sku', 'region').order_by('-date').first()
        if latest_price:
            latest_prices.append(latest_price)
    
    # All recent orders (buyer head can see all)
    recent_orders = Order.objects.select_related(
        'farmer__user', 'assigned_buyer', 'sku'
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
    
    # Latest prices (MySQL-compatible approach)
    # Get latest price per SKU-region combination
    latest_prices = []
    sku_region_combinations = FarmerPrice.objects.values('sku', 'region').distinct()
    
    for combo in sku_region_combinations[:15]:
        latest_price = FarmerPrice.objects.filter(
            sku=combo['sku'], 
            region=combo['region']
        ).select_related('farmer__user', 'sku', 'region').order_by('-date').first()
        if latest_price:
            latest_prices.append(latest_price)
    
    # Base QuerySet for orders created by this buyer
    my_orders_base = Order.objects.filter(
        ordered_by=user
    ).select_related('farmer__user', 'sku')
    
    # Recent orders for display (sliced)
    my_orders = my_orders_base.order_by('-created_at')[:10]
    
    # Buyer-specific stats (using base QuerySet)
    buyer_stats = {
        'my_orders': my_orders_base.count(),
        'pending_orders': my_orders_base.filter(status='pending').count(),
        'weekly_orders': my_orders_base.filter(created_at__gte=week_ago).count(),
        'total_spent': my_orders_base.filter(
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
        farmer_score = FarmerScore.objects.get(farmer=farmer, is_current=True)
        # Calculate rank by counting how many farmers have higher scores
        current_rank = FarmerScore.objects.filter(
            is_current=True,
            total_score__gt=farmer_score.total_score
        ).count() + 1
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


class CustomLoginView(auth_views.LoginView):
    """Custom login view with redirect logic"""
    template_name = 'registration/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        return reverse_lazy('core:dashboard')
    
    def form_valid(self, form):
        return super().form_valid(form)


class CustomLogoutView(auth_views.LogoutView):
    """Custom logout view"""
    next_page = reverse_lazy('accounts:login')
    
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


@admin_required
def admin_settings(request):
    """Admin settings page"""
    context = {
        'title': _('Admin Settings'),
        'user': request.user,
    }
    return render(request, 'core/admin_settings.html', context)

@admin_required
def bulk_upload_sku(request):
    """Bulk upload SKUs from text or CSV"""
    context = {
        'title': _('Bulk Upload SKUs'),
        'user': request.user,
    }
    
    if request.method == 'POST':
        upload_type = request.POST.get('upload_type', 'text')
        
        if upload_type == 'text':
            # Handle text input
            sku_text = request.POST.get('sku_text', '').strip()
            if sku_text:
                result = process_sku_text(sku_text)
                context.update(result)
                
        elif upload_type == 'csv' and request.FILES.get('csv_file'):
            # Handle CSV upload
            csv_file = request.FILES['csv_file']
            result = process_sku_csv(csv_file)
            context.update(result)
            
        elif upload_type == 'predefined':
            # Handle predefined list upload
            result = upload_predefined_skus()
            context.update(result)
    
    return render(request, 'core/bulk_upload_sku.html', context)


def process_sku_text(sku_text):
    """Process SKU names from text input"""
    lines = [line.strip() for line in sku_text.split('\n') if line.strip()]
    created_count = 0
    skipped_count = 0
    errors = []
    created_skus = []
    
    for line in lines:
        try:
            # Generate SKU code from name
            sku_code = generate_sku_code(line)
            
            # Check if SKU already exists
            if SKU.objects.filter(code=sku_code).exists():
                skipped_count += 1
                continue
                
            # Determine category based on name
            category = determine_category(line)
            
            # Create SKU
            sku = SKU.objects.create(
                code=sku_code,
                name=line,
                category=category,
                unit='kg',  # Default unit
                is_active=True
            )
            created_skus.append(sku)
            created_count += 1
            
        except Exception as e:
            errors.append(f"Error creating '{line}': {str(e)}")
    
    return {
        'upload_success': True,
        'created_count': created_count,
        'skipped_count': skipped_count,
        'errors': errors,
        'created_skus': created_skus
    }


def process_sku_csv(csv_file):
    """Process SKU data from CSV file"""
    try:
        # Read CSV file
        decoded_file = csv_file.read().decode('utf-8')
        csv_data = csv.DictReader(io.StringIO(decoded_file))
        
        created_count = 0
        skipped_count = 0
        errors = []
        created_skus = []
        
        for row in csv_data:
            try:
                name = row.get('name', '').strip()
                if not name:
                    continue
                
                sku_code = row.get('code', generate_sku_code(name))
                category = row.get('category', determine_category(name))
                unit = row.get('unit', 'kg')
                
                # Check if SKU already exists
                if SKU.objects.filter(code=sku_code).exists():
                    skipped_count += 1
                    continue
                
                # Create SKU
                sku = SKU.objects.create(
                    code=sku_code,
                    name=name,
                    category=category,
                    unit=unit,
                    description=row.get('description', ''),
                    is_active=True
                )
                created_skus.append(sku)
                created_count += 1
                
            except Exception as e:
                errors.append(f"Error processing row: {str(e)}")
        
        return {
            'upload_success': True,
            'created_count': created_count,
            'skipped_count': skipped_count,
            'errors': errors,
            'created_skus': created_skus
        }
        
    except Exception as e:
        return {
            'upload_success': False,
            'errors': [f"Error reading CSV file: {str(e)}"]
        }


def upload_predefined_skus():
    """Upload the predefined list of SKUs"""
    predefined_skus = [
        "Coconut", "Onion Big", "Tomato Country", "Carrot", "Pomegranate", "Potato",
        "Onion Sambar", "Tomato Hybrid", "Banana Nendran", "Beetroot", "Guava Thailand",
        "Apple Envy", "Cucumber Salad", "Apple Himachal Indian", "Ginger Fresh",
        "Apple Royal Gala", "Lemon", "Mango Neelam", "Orange Imported", "Beans French",
        "Ladies Finger", "Cauliflower", "Water Melon Kiran", "Chilli Green",
        "Garlic Himachal", "Banana Green Nendran", "Apple Red Delicious", "Cucumber Malabar",
        "Garlic Small", "American Sweet Corn Pack Of 2", "Dragon Fruit Red Indian Kg",
        "Pine Apple", "Apple Pink Lady", "Strawberry", "Garlic Big", "Mini Orange",
        "Gooseberry amla", "Cabbage", "Drum Stick", "Corriander Leaves", "Capsicum Green",
        "Brinjal Vari", "Kiwi Pack Of 3", "Coccinia", "Apple Granny Smith", "Papaya",
        "Chilli Thondan", "Banana Raw", "Chilli Bullet", "Apple Fuji", "Mango Raw",
        "Avacado Imported", "Sweet Potato", "Button Mushroom", "Dragon Fruit White",
        "American Sweet Corn Pc", "Snake Gourd", "Cucumber English", "Pear Red",
        "Banana Yellaki Rasakathali", "Blue Berry Imported", "Plums Indain", "Avacado",
        "Apple New Zealand Royal Gala", "Grapes Imported", "Beans Cowpea Long",
        "Bitter Gourd White", "Mango Raw Totapuri", "Pumpkin", "Pears Indian",
        "Beans Haricot", "Apple Shimla Indian", "Pomegranate Medium Kg",
        "Apple Washington Red", "Spinach Palak Bunch", "Bottle Gourd", "Yam",
        "Musk Melon", "Beans Cluster", "Rambutan", "Plums Imported", "Mint Leaves",
        "Colacasia Big", "Grapes Red Globe Indian", "Guava White", "Sweet Orange",
        "Bitter Gourd Green", "Tapioca", "Banana Red Kappa", "Grapes Dilkush",
        "Cucumber Madras", "Beans Avarai Small", "Broccoli", "Grapes Panner",
        "Banana Robusta Green", "Oyster Mushroom", "Koorka", "Grapes Banglore Blue",
        "Chilli bhajji", "Banana Karpooravalli", "Banana Robusta Yellow",
        "Brinjal Long Green", "Banana Poovan", "Brinjal Nadan", "Curry Leaves",
        "Banana Palayamthodan", "Amaranthus Green Bunch", "Ash Gourd", "Apple Goru",
        "Ground Nut", "Chow Chow", "Ridge Gourd", "Radish White", "Pear Green",
        "White Egg 6PC", "Beans Cowpea Small", "Water apple", "Colacasia Small",
        "Custard Apple", "Lettuce Ice Berg", "Amaranthus Red Bunch", "Chinese Cabbage",
        "Apple I Red", "Golden Kiwi 3Pc", "Apple Granny 4 Pcs", "Sapota  Cricket Ball",
        "Cabbage Red", "Sapota Hybrid", "Country Egg 6PC", "Mangosteen",
        "Capsicum Color", "Banana Flower", "Orange Nagpur", "Apple Granny 2 Pcs",
        "Apple Royal Gala 2 Pcs", "Snake Gourd Long", "Pumpkin Red",
        "Orange Mandarin 500gm", "Agathi Keera Bunch", "Grapes green imported",
        "Mango Totapuri", "Milky Mushroom", "Brinjal White", "Sambar Kit",
        "Baby Potato", "Apple Royal Gala 4 Pcs", "Jujube Fruit", "Veg Biryani Pack 250g",
        "Apple Pink lady 4 Pcs", "Spring Onion", "Plums imported 4 Pcs", "Zucchini Green",
        "Ponnanganni Keerai Bunch", "Baby Corn Unpleed", "Banana Leaves pc",
        "Sweet tamarind", "Zucchini Yellow", "Fresh Mango Juice 250ml", "Dragon Fruit Red",
        "Cut Fruit Mix", "Grapes Sonaka Seedless", "Tn Beetroot", "Dragon Fruit Yelllow Kg",
        "Mango Sindhura", "Spring Onion Pc", "Celery", "Grapes Balck Seedless",
        "Leek", "Fresh fig", "Litchi", "Sour passion fruit Kg", "Lemon Big",
        "Mango Imam", "KARUNAI KILANGU", "Knolkhol Kg", "Bitter Gourd Nadan",
        "Coriander Kg", "Mango Dasheri", "Marigold Flower", "Pineapple Small",
        "Water Melon", "Fresh pigeon pea Kg", "Apple Kashmir Red Delicious",
        "Basil Leaves", "Fried Rice Mix 300g", "Baby Corn Peeled", "Lettuce Head Bunch-Kg",
        "Rosemary", "American Sweetcorn Peeled-Unit", "Micro Radish", "Sun Melon",
        "Tn Cabbage", "Tender Jack Fruit"
    ]
    
    return process_sku_text('\n'.join(predefined_skus))


def generate_sku_code(name):
    """Generate SKU code from product name"""
    # Remove special characters and convert to uppercase
    clean_name = re.sub(r'[^a-zA-Z0-9\s]', '', name)
    words = clean_name.split()
    
    if len(words) == 1:
        # Single word: take first 6 characters
        code = words[0][:6].upper()
    elif len(words) == 2:
        # Two words: take first 3 chars of each
        code = (words[0][:3] + words[1][:3]).upper()
    else:
        # Multiple words: take first 2 chars of first 3 words
        code = ''.join([word[:2] for word in words[:3]]).upper()
    
    # Ensure minimum length of 4 characters
    if len(code) < 4:
        code = code + '0' * (4 - len(code))
    
    # Ensure uniqueness by adding number suffix if needed
    base_code = code[:6]  # Limit to 6 chars for base
    counter = 1
    final_code = base_code
    
    while SKU.objects.filter(code=final_code).exists():
        final_code = f"{base_code}{counter:02d}"
        counter += 1
        if len(final_code) > 20:  # Prevent infinite loop
            break
    
    return final_code


def determine_category(name):
    """Determine product category based on name"""
    name_lower = name.lower()
    
    # Fruit keywords
    fruit_keywords = [
        'apple', 'mango', 'banana', 'orange', 'lemon', 'grape', 'strawberry',
        'pineapple', 'papaya', 'guava', 'pomegranate', 'kiwi', 'dragon fruit',
        'watermelon', 'melon', 'pear', 'plum', 'avocado', 'coconut', 'fig',
        'litchi', 'rambutan', 'mangosteen', 'custard apple', 'gooseberry',
        'amla', 'jujube', 'tamarind', 'passion fruit'
    ]
    
    # Spice/herb keywords
    spice_keywords = [
        'ginger', 'garlic', 'chilli', 'coriander', 'mint', 'basil', 'rosemary',
        'curry leaves'
    ]
    
    # Check for fruits
    for keyword in fruit_keywords:
        if keyword in name_lower:
            return 'fruit'
    
    # Check for spices
    for keyword in spice_keywords:
        if keyword in name_lower:
            return 'spice'
    
    # Check for specific vegetable patterns
    if any(word in name_lower for word in ['egg', 'mushroom']):
        return 'other'
    
    # Default to vegetable
    return 'vegetable'


@admin_required  
@require_http_methods(["GET"])
def download_sku_template(request):
    """Download CSV template for SKU bulk upload"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="sku_template.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['name', 'code', 'category', 'unit', 'description'])
    writer.writerow(['Apple Red Delicious', 'APPLE01', 'fruit', 'kg', 'Fresh red delicious apples'])
    writer.writerow(['Tomato Country', 'TOMATO01', 'vegetable', 'kg', 'Local variety tomatoes'])
    
    return response
