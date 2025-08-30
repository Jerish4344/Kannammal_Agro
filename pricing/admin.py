from django.contrib import admin
from django import forms
from django.utils import timezone
from .models import FarmerPrice


class FarmerPriceAdminForm(forms.ModelForm):
    """Custom form for FarmerPrice admin with better date handling."""
    
    date = forms.DateField(
        widget=forms.DateInput(
            attrs={
                'type': 'date',
                'class': 'vDateField'
            }
        ),
        required=True
    )
    
    class Meta:
        model = FarmerPrice
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default date to today if creating new record
        if not self.instance.pk:
            self.fields['date'].initial = timezone.now().date()
        
        # Make region auto-populate based on farmer selection
        if 'farmer' in self.data and not self.instance.pk:
            try:
                farmer_id = int(self.data['farmer'])
                from farmers.models import Farmer
                farmer = Farmer.objects.get(pk=farmer_id)
                self.fields['region'].initial = farmer.region
            except (ValueError, Farmer.DoesNotExist):
                pass


@admin.register(FarmerPrice)
class FarmerPriceAdmin(admin.ModelAdmin):
    form = FarmerPriceAdminForm
    list_display = ('get_farmer_name', 'region', 'sku', 'date', 'price', 'quantity_available', 'is_active', 'submitted_at')
    list_filter = ('sku__category', 'is_active', 'submitted_at', 'farmer__region')
    search_fields = ('farmer__user__first_name', 'farmer__user__last_name', 'sku__name', 'sku__code')
    ordering = ('-submitted_at',)
    
    fieldsets = (
        ('Pricing Information', {
            'fields': ('farmer', 'region', 'sku', 'date', 'price', 'quantity_available'),
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
    
    def save_model(self, request, obj, form, change):
        """Custom save to ensure all required fields are set."""
        from django.utils import timezone
        
        # Ensure date is set
        if not obj.date:
            obj.date = timezone.now().date()
        
        # Ensure region is set based on farmer
        if not obj.region and obj.farmer:
            obj.region = obj.farmer.region
            
        super().save_model(request, obj, form, change)
    
    def get_farmer_name(self, obj):
        return f"{obj.farmer.user.first_name} {obj.farmer.user.last_name}" if obj.farmer.user.first_name else obj.farmer.user.username
    get_farmer_name.short_description = 'Farmer'
    get_farmer_name.admin_order_field = 'farmer__user__first_name'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('farmer__user', 'sku')
