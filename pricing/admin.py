from django.contrib import admin
from .models import FarmerPrice

@admin.register(FarmerPrice)
class FarmerPriceAdmin(admin.ModelAdmin):
    list_display = ('get_farmer_name', 'sku', 'price', 'quantity_available', 'is_active', 'submitted_at')
    list_filter = ('sku__category', 'is_active', 'submitted_at', 'farmer__region')
    search_fields = ('farmer__user__first_name', 'farmer__user__last_name', 'sku__name', 'sku__code')
    ordering = ('-submitted_at',)
    
    fieldsets = (
        ('Pricing Information', {
            'fields': ('farmer', 'sku', 'price', 'quantity_available'),
        }),
        ('Details', {
            'fields': ('notes',),
        }),
        ('Submission', {
            'fields': ('submitted_via', 'voice_transcript'),
        }),
        ('Status', {
            'fields': ('is_active',),
        }),
    )
    
    readonly_fields = ('submitted_at', 'created_at', 'updated_at')
    
    def get_farmer_name(self, obj):
        return f"{obj.farmer.user.first_name} {obj.farmer.user.last_name}" if obj.farmer.user.first_name else obj.farmer.user.username
    get_farmer_name.short_description = 'Farmer'
    get_farmer_name.admin_order_field = 'farmer__user__first_name'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('farmer__user', 'sku')
