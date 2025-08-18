from django.contrib import admin
from .models import Region

@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'code')
    ordering = ('name',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'code'),
        }),
        ('Details', {
            'fields': ('description',),
        }),
        ('Status', {
            'fields': ('is_active',),
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
