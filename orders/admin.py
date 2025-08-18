from django.contrib import admin
from .models import Order

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'get_farmer_name', 'sku', 'quantity', 'status', 'total_amount', 'created_at')
    list_filter = ('status', 'created_at', 'expected_delivery_date')
    search_fields = ('order_number', 'farmer__user__first_name', 'farmer__user__last_name', 'sku__name')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'farmer', 'sku', 'quantity', 'unit_price'),
        }),
        ('Order Details', {
            'fields': ('status', 'total_amount', 'notes'),
        }),
        ('Assignment', {
            'fields': ('ordered_by', 'approved_by', 'assigned_buyer'),
        }),
        ('Delivery', {
            'fields': ('expected_delivery_date', 'actual_delivery_date'),
        }),
    )
    
    readonly_fields = ('order_number', 'created_at', 'updated_at', 'total_amount')
    
    def get_farmer_name(self, obj):
        return f"{obj.farmer.user.first_name} {obj.farmer.user.last_name}" if obj.farmer.user.first_name else obj.farmer.user.username
    get_farmer_name.short_description = 'Farmer'
    get_farmer_name.admin_order_field = 'farmer__user__first_name'
