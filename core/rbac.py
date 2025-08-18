"""Role-based access control mixins and decorators."""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps


class RoleRequiredMixin(LoginRequiredMixin):
    """Mixin to require specific roles for access."""
    
    required_roles = []  # List of roles that can access this view
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        if not any(getattr(request.user, f'is_{role}', False) for role in self.required_roles):
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('dashboard')
        
        return super().dispatch(request, *args, **kwargs)


class AdminRequiredMixin(RoleRequiredMixin):
    """Mixin to require admin role."""
    required_roles = ['admin']


class RegionHeadRequiredMixin(RoleRequiredMixin):
    """Mixin to require region head role."""
    required_roles = ['admin', 'region_head']


class BuyerHeadRequiredMixin(RoleRequiredMixin):
    """Mixin to require buyer head role."""
    required_roles = ['admin', 'buyer_head']


class BuyerRequiredMixin(RoleRequiredMixin):
    """Mixin to require buyer role (includes buyer_head)."""
    required_roles = ['admin', 'buyer_head', 'buyer']


class FarmerRequiredMixin(RoleRequiredMixin):
    """Mixin to require farmer role."""
    required_roles = ['admin', 'farmer']


def role_required(*roles):
    """Decorator to require specific roles for function views."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('accounts:login')
            
            if not any(getattr(request.user, f'is_{role}', False) for role in roles):
                messages.error(request, 'You do not have permission to access this page.')
                return redirect('dashboard')
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def admin_required(view_func):
    """Decorator to require admin role."""
    return role_required('admin')(view_func)


def region_head_required(view_func):
    """Decorator to require region head role."""
    return role_required('admin', 'region_head')(view_func)


def buyer_required(view_func):
    """Decorator to require buyer role."""
    return role_required('admin', 'buyer_head', 'buyer')(view_func)


def farmer_required(view_func):
    """Decorator to require farmer role."""
    return role_required('admin', 'farmer')(view_func)
