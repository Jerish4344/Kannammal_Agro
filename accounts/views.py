from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

# Create your views here.

@login_required
def profile_view(request):
    """User profile view"""
    return render(request, 'accounts/profile.html', {})

@login_required
def profile_edit(request):
    """Edit user profile"""
    return render(request, 'accounts/profile_edit.html', {})

@login_required 
def user_list(request):
    """List all users - admin only"""
    return HttpResponse("User list - TODO")

@login_required
def user_create(request):
    """Create new user - admin only"""  
    return HttpResponse("Create user - TODO")

@login_required
def user_detail(request, pk):
    """User detail view - admin only"""
    return HttpResponse(f"User detail {pk} - TODO")
