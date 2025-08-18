"""URL patterns for farmers app."""

from django.urls import path
from . import views

app_name = 'farmers'

urlpatterns = [
    # Farmer management (for admin/buyer_head)
    path('', views.farmer_list, name='list'),
    
    # Farmer self-service
    path('my-profile/', views.my_profile, name='my_profile'),
]
