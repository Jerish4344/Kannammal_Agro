from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from accounts.models import User

try:
    from regions.models import Region
except ImportError:
    Region = None

try:
    from catalog.models import SKU
except ImportError:
    SKU = None

try:
    from farmers.models import Farmer
except ImportError:
    Farmer = None

try:
    from pricing.models import FarmerPrice
except ImportError:
    FarmerPrice = None

try:
    from orders.models import Order
except ImportError:
    Order = None

@login_required
@require_http_methods(["GET"])
def farmers_api(request):
    """API endpoint to get farmers data"""
    if not Farmer:
        return JsonResponse([{'error': 'Farmers model not available'}], safe=False)
    
    farmers = Farmer.objects.select_related('region', 'user').all()
    
    farmers_data = []
    for farmer in farmers:
        farmers_data.append({
            'id': farmer.id,
            'farmer_id': farmer.farmer_id,
            'name': farmer.user.get_full_name() or farmer.user.username if farmer.user else 'Unknown',
            'phone': farmer.contact_number,
            'region': farmer.region.name if farmer.region else '-',
            'farm_size': str(farmer.farm_size) if farmer.farm_size else '-',
            'is_verified': farmer.is_verified,
            'created_at': farmer.created_at.strftime('%Y-%m-%d %H:%M') if hasattr(farmer, 'created_at') else '-',
        })
    
    return JsonResponse(farmers_data, safe=False)

@login_required
@require_http_methods(["GET"])
def prices_api(request):
    """API endpoint to get prices data"""
    if not FarmerPrice:
        return JsonResponse([{'error': 'FarmerPrice model not available'}], safe=False)
    
    prices = FarmerPrice.objects.select_related('farmer__user', 'sku').all()[:50]  # Limit to 50 for performance
    
    prices_data = []
    for price in prices:
        farmer_name = '-'
        if price.farmer and price.farmer.user:
            farmer_name = price.farmer.user.get_full_name() or price.farmer.user.username
        
        prices_data.append({
            'id': price.id,
            'farmer': farmer_name,
            'sku': price.sku.name if price.sku else '-',
            'price': f'₹{price.price}' if hasattr(price, 'price') else '-',
            'date': price.date.strftime('%Y-%m-%d') if hasattr(price, 'date') else (price.created_at.strftime('%Y-%m-%d') if hasattr(price, 'created_at') else '-'),
            'quantity_available': f'{price.quantity_available} kg' if price.quantity_available else '-',
        })
    
    return JsonResponse(prices_data, safe=False)

@login_required
@require_http_methods(["GET"])
def orders_api(request):
    """API endpoint to get orders data"""
    if not Order:
        return JsonResponse([{'error': 'Order model not available'}], safe=False)
    
    orders = Order.objects.select_related('farmer__user', 'sku').all()[:50]  # Limit to 50 for performance
    
    orders_data = []
    for order in orders:
        farmer_name = '-'
        if order.farmer and order.farmer.user:
            farmer_name = order.farmer.user.get_full_name() or order.farmer.user.username
        
        orders_data.append({
            'id': order.id,
            'order_number': getattr(order, 'order_number', '-'),
            'farmer': farmer_name,
            'sku': order.sku.name if order.sku else '-',
            'quantity': f'{order.quantity} kg' if hasattr(order, 'quantity') else '-',
            'unit_price': f'₹{order.unit_price}' if hasattr(order, 'unit_price') else '-',
            'total_value': f'₹{order.total_value}' if hasattr(order, 'total_value') else '-',
            'status': getattr(order, 'status', '-'),
            'date': order.created_at.strftime('%Y-%m-%d') if hasattr(order, 'created_at') else '-',
        })
    
    return JsonResponse(orders_data, safe=False)

@login_required
@require_http_methods(["GET"])
def users_api(request):
    """API endpoint to get users data"""
    users = User.objects.all()
    
    users_data = []
    for user in users:
        users_data.append({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'is_active': user.is_active,
            'date_joined': user.date_joined.strftime('%Y-%m-%d'),
        })
    
    return JsonResponse(users_data, safe=False)

@login_required
@require_http_methods(["GET"])
def dashboard_stats_api(request):
    """API endpoint to get dashboard statistics"""
    stats = {
        'total_farmers': Farmer.objects.count() if Farmer else 0,
        'total_users': User.objects.count(),
        'total_orders': Order.objects.count() if Order else 0,
        'total_skus': SKU.objects.count() if SKU else 0,
        'recent_prices': FarmerPrice.objects.count() if FarmerPrice else 0,
        'regions': Region.objects.count() if Region else 0,
    }
    
    return JsonResponse(stats)
