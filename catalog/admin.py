from django.contrib import admin
from .models import SKU

@admin.register(SKU)
class SKUAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'category', 'unit', 'is_active', 'created_at')
    list_filter = ('category', 'unit', 'is_active', 'created_at')
    search_fields = ('name', 'code', 'description')
    ordering = ('category', 'name')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'code', 'category'),
        }),
        ('Localization', {
            'fields': ('name_ta', 'name_hi'),
        }),
        ('Product Details', {
            'fields': ('description', 'unit', 'specifications'),
        }),
        ('Status', {
            'fields': ('is_active',),
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
