"""URL patterns for ranking app."""

from django.urls import path

from . import views

app_name = 'ranking'

urlpatterns = [
    # Farmer ranking board
    path('board/', views.ranking_board, name='ranking_board'),
    path('weekly/', views.weekly_rankings, name='weekly_rankings'),
    path('monthly/', views.monthly_rankings, name='monthly_rankings'),
    path('history/', views.ranking_history, name='ranking_history'),
]
