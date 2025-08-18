"""URL patterns for reports app."""

from django.urls import path

from . import views

app_name = 'reports'

urlpatterns = [
    # Report dashboard
    path('', views.dashboard, name='dashboard'),
    path('sales/', views.sales_report, name='sales_report'),
    path('farmer/', views.farmer_report, name='farmer_report'),
    path('export/', views.export_report, name='export_report'),
]
