from django.contrib import admin
from .models import Farmer

@admin.register(Farmer)
class FarmerAdmin(admin.ModelAdmin):
    list_display = ('get_farmer_id', 'get_farmer_name', 'get_farmer_email', 'region', 'contact_number', 'is_active', 'created_at')
    list_filter = ('region', 'is_active', 'created_at')
    search_fields = ('user__first_name', 'user__last_name', 'user__email', 'user__username', 'contact_number')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',),
        }),
        ('Contact Details', {
            'fields': ('contact_number', 'alternate_contact', 'address'),
        }),
        ('Location', {
            'fields': ('region',),
        }),
        ('Farm Information', {
            'fields': ('farm_size', 'farm_type'),
        }),
        ('Banking', {
            'fields': ('bank_account_number', 'bank_ifsc', 'bank_name'),
        }),
        ('Status', {
            'fields': ('is_active',),
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def get_farmer_id(self, obj):
        return f"F{obj.id:04d}"
    get_farmer_id.short_description = 'Farmer ID'
    get_farmer_id.admin_order_field = 'id'
    
    def get_farmer_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}" if obj.user.first_name else obj.user.username
    get_farmer_name.short_description = 'Name'
    get_farmer_name.admin_order_field = 'user__first_name'
    
    def get_farmer_email(self, obj):
        return obj.user.email
    get_farmer_email.short_description = 'Email'
    get_farmer_email.admin_order_field = 'user__email'
