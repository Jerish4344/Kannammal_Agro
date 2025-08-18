from django.urls import path
from . import views, api_views

app_name = 'core'

urlpatterns = [
    # Main views
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # API endpoints
    path('api/farmers/', api_views.farmers_api, name='farmers_api'),
    path('api/prices/', api_views.prices_api, name='prices_api'),
    path('api/orders/', api_views.orders_api, name='orders_api'),
    path('api/users/', api_views.users_api, name='users_api'),
    path('api/stats/', api_views.dashboard_stats_api, name='dashboard_stats_api'),
]
