"""
URL configuration for kannammal_agro project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.views.i18n import set_language

urlpatterns = [
    # Language switching endpoint (outside i18n_patterns)
    path('i18n/set-language/', set_language, name='set_language'),
    
    # Admin interface
    path('admin/', admin.site.urls),
    
    # Health check
    path('health/', lambda request: 
         __import__('django.http', fromlist=['HttpResponse']).HttpResponse('OK')),
]

# Internationalized URL patterns
urlpatterns += i18n_patterns(
    # Core URLs
    path('', include('core.urls')),
    
    # App URLs
    path('accounts/', include('accounts.urls')),
    path('farmers/', include('farmers.urls')),
    path('pricing/', include('pricing.urls')),
    path('orders/', include('orders.urls')),
    path('regions/', include('regions.urls')),
    path('catalog/', include('catalog.urls')),
    path('ranking/', include('ranking.urls')),
    path('reports/', include('reports.urls')),
    path('notifications/', include('notifications.urls')),
    
    prefix_default_language=False,
)

# Static and media files
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
