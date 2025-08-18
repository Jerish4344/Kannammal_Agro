from django.contrib import admin
from .models import FarmerScore

@admin.register(FarmerScore)
class FarmerScoreAdmin(admin.ModelAdmin):
    list_display = ('get_farmer_name', 'total_score', 'consistency_score', 'reliability_score', 'is_current')
    list_filter = ('is_current', 'region', 'created_at')
    search_fields = ('farmer__user__first_name', 'farmer__user__last_name', 'farmer__user__username')
    ordering = ('-total_score',)
    
    fieldsets = (
        ('Farmer Information', {
            'fields': ('farmer', 'region'),
        }),
        ('Scores', {
            'fields': ('total_score', 'consistency_score', 'reliability_score', 'fill_rate_score'),
        }),
        ('Metrics', {
            'fields': ('total_prices_submitted', 'on_time_submissions', 'total_orders', 'on_time_deliveries'),
        }),
        ('Status', {
            'fields': ('is_current',),
        }),
    )
    
    readonly_fields = ('computed_at', 'created_at', 'updated_at')
    
    def get_farmer_name(self, obj):
        return f"{obj.farmer.user.first_name} {obj.farmer.user.last_name}" if obj.farmer.user.first_name else obj.farmer.user.username
    get_farmer_name.short_description = 'Farmer'
    get_farmer_name.admin_order_field = 'farmer__user__first_name'
