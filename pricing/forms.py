"""
Forms for price submission functionality.
"""
from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal

from .models import FarmerPrice
from catalog.models import SKU


class PriceSubmissionForm(forms.ModelForm):
    """Form for farmers to submit prices"""
    
    class Meta:
        model = FarmerPrice
        fields = [
            'sku', 'price', 'quantity_available', 
            'submitted_via', 'notes'
        ]
        widgets = {
            'sku': forms.Select(attrs={
                'class': 'form-select searchable-select', 
                'id': 'id_sku',
                'data-placeholder': 'Search and select a product...'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-input',
                'step': '0.01',
                'min': '0',
                'placeholder': _('Enter price per unit')
            }),
            'quantity_available': forms.NumberInput(attrs={
                'class': 'form-input',
                'step': '0.01',
                'min': '0',
                'placeholder': _('Enter available quantity')
            }),
            'submitted_via': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3}),
        }
        labels = {
            'sku': _('Product (SKU)'),
            'price': _('Price per Unit'),
            'quantity_available': _('Available Quantity'),
            'submitted_via': _('Submission Method'),
            'notes': _('Notes'),
        }
    
    def __init__(self, *args, **kwargs):
        self.farmer = kwargs.pop('farmer', None)
        super().__init__(*args, **kwargs)
        
        # Only show active SKUs
        self.fields['sku'].queryset = SKU.objects.filter(is_active=True).order_by('name')
        
        # Add help text
        self.fields['price'].help_text = _('Price in local currency per unit')
        self.fields['quantity_available'].help_text = _('Total quantity available for sale')
        self.fields['notes'].help_text = _('Additional information about your produce')
    
    def clean(self):
        cleaned_data = super().clean()
        sku = cleaned_data.get('sku')
        price = cleaned_data.get('price')
        farmer = self.farmer
        
        # Check if farmer already submitted price for this SKU today
        if sku and farmer:
            today = timezone.now().date()
            existing_price = FarmerPrice.objects.filter(
                farmer=farmer,
                sku=sku,
                date=today
            ).exists()
            
            if existing_price:
                raise ValidationError(
                    _('You have already submitted a price for {} today.').format(sku.name)
                )
        
        return cleaned_data
    
    def save(self, commit=True):
        """Save the price submission"""
        farmer_price = super().save(commit=False)
        farmer_price.date = timezone.now().date()
        
        if commit:
            farmer_price.save()
        
        return farmer_price


class PriceFilterForm(forms.Form):
    """Form for filtering price comparisons"""
    
    sku = forms.ModelChoiceField(
        queryset=SKU.objects.filter(is_active=True),
        required=False,
        label=_('Product'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    date_range = forms.ChoiceField(
        choices=[
            ('today', _('Today')),
            ('week', _('Last 7 days')),
            ('month', _('Last 30 days')),
        ],
        required=False,
        initial='today',
        label=_('Date Range'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Add region filter for admin users
        if self.user and self.user.role == 'admin':
            from regions.models import Region
            self.fields['region'] = forms.ModelChoiceField(
                queryset=Region.objects.filter(is_active=True),
                required=False,
                label=_('Region'),
                widget=forms.Select(attrs={'class': 'form-select'})
            )
