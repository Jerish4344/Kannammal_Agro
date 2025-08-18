from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# Create your views here.

@login_required
def ranking_board(request):
    """Display ranking board"""
    return render(request, 'ranking/board.html', {})

@login_required
def weekly_rankings(request):
    """Display weekly rankings"""
    return render(request, 'ranking/weekly.html', {})

@login_required
def monthly_rankings(request):
    """Display monthly rankings"""
    return render(request, 'ranking/monthly.html', {})

@login_required
def ranking_history(request):
    """Display ranking history"""
    return render(request, 'ranking/history.html', {})
