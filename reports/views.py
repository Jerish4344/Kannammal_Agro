from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# Create your views here.

@login_required 
def dashboard(request):
    """Reports dashboard"""
    return render(request, 'reports/dashboard.html', {})

@login_required
def sales_report(request):
    """Sales report"""
    return render(request, 'reports/sales.html', {})

@login_required
def farmer_report(request):
    """Farmer report"""
    return render(request, 'reports/farmer.html', {})

@login_required
def export_report(request):
    """Export report"""
    return render(request, 'reports/export.html', {})
