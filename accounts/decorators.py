"""
Decorators for role-based access control.
"""
from functools import wraps
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages
from django.utils.translation import gettext as _


def role_required(allowed_roles):
    """
    Decorator that checks if user has one of the allowed roles.
    
    Usage:
        @role_required(['admin', 'buyer_head'])
        def my_view(request):
            pass
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if request.user.role in allowed_roles:
                return view_func(request, *args, **kwargs)
            else:
                messages.error(
                    request,
                    _('You do not have permission to access this page.')
                )
                return redirect('core:dashboard')
        return _wrapped_view
    return decorator


def admin_required(view_func):
    """Decorator that requires admin role"""
    return role_required(['admin'])(view_func)


def buyer_head_required(view_func):
    """Decorator that requires buyer_head role"""
    return role_required(['buyer_head'])(view_func)


def farmer_required(view_func):
    """Decorator that requires farmer role"""
    return role_required(['farmer'])(view_func)


def region_access_required(view_func):
    """
    Decorator that checks if user can access data from the requested region.
    For admin users: access to all regions
    For other roles: access only to their assigned region
    """
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        user = request.user
        
        # Get region from URL parameters or POST data
        requested_region = kwargs.get('region_code') or request.GET.get('region') or request.POST.get('region')
        
        if user.role == 'admin':
            # Admin can access all regions
            return view_func(request, *args, **kwargs)
        elif requested_region and user.region and user.region.code != requested_region:
            # User trying to access different region
            messages.error(
                request,
                _('You do not have permission to access data from this region.')
            )
            return redirect('core:dashboard')
        else:
            return view_func(request, *args, **kwargs)
    
    return _wrapped_view


class RoleRequiredMixin:
    """
    Mixin for class-based views that requires specific roles.
    
    Usage:
        class MyView(RoleRequiredMixin, TemplateView):
            allowed_roles = ['admin', 'buyer_head']
    """
    allowed_roles = []
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        if request.user.role not in self.allowed_roles:
            messages.error(
                request,
                _('You do not have permission to access this page.')
            )
            return redirect('core:dashboard')
        
        return super().dispatch(request, *args, **kwargs)
    
    def handle_no_permission(self):
        return redirect('login')


class RegionAccessMixin:
    """
    Mixin for class-based views that checks region access.
    """
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        user = request.user
        requested_region = kwargs.get('region_code') or request.GET.get('region')
        
        if user.role != 'admin' and requested_region and user.region and user.region.code != requested_region:
            messages.error(
                request,
                _('You do not have permission to access data from this region.')
            )
            return redirect('core:dashboard')
        
        return super().dispatch(request, *args, **kwargs)
