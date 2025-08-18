"""URL patterns for pricing app."""

from django.urls import path

from . import views

app_name = 'pricing'

urlpatterns = [
    # Price submission for farmers
    path('submit/', views.submit_price, name='submit_price'),
    
    # Price comparison
    path('comparison/', views.price_comparison, name='comparison'),
    
    # Price management  
    path('', views.price_comparison, name='price_list'),
    path('history/', views.my_price_history, name='price_history'),
    
    # Exports
    path('export/', views.export_prices, name='export_prices'),
    
    # API endpoints
    path('api/sku/<int:sku_id>/', views.api_sku_info, name='api_sku_info'),
]
