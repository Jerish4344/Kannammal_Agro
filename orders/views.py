from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

# Create your views here.

@login_required
def order_list(request):
    """List all orders"""
    return render(request, 'orders/order_list.html', {})

@login_required
def order_create(request):
    """Create new order"""
    return render(request, 'orders/order_create.html', {})

@login_required
def order_detail(request, pk):
    """Order detail view"""
    return render(request, 'orders/order_detail.html', {})

@login_required
def order_edit(request, pk):
    """Edit order"""
    return render(request, 'orders/order_edit.html', {})

@login_required
def order_confirm(request, pk):
    """Confirm order"""
    return HttpResponse("Order confirm")

@login_required
def order_assign(request, pk):
    """Assign order"""
    return HttpResponse("Order assign")

@login_required
def order_status_update(request, pk):
    """Update order status"""
    return HttpResponse("Order status update")

@login_required
def order_payment(request, pk):
    """Order payment"""
    return HttpResponse("Order payment")
