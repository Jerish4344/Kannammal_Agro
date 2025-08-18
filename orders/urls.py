"""URL patterns for orders app."""

from django.urls import path

from . import views

app_name = 'orders'

urlpatterns = [
    # Order management
    path('', views.order_list, name='order_list'),
    path('new/', views.order_create, name='order_create'),
    path('<int:pk>/', views.order_detail, name='order_detail'),
    path('<int:pk>/edit/', views.order_edit, name='order_edit'),
    path('<int:pk>/confirm/', views.order_confirm, name='order_confirm'),
    path('<int:pk>/assign/', views.order_assign, name='order_assign'),
    path('<int:pk>/status/', views.order_status_update, name='order_status_update'),
    
    # Payment management
    path('<int:pk>/payment/', views.order_payment, name='order_payment'),
]
