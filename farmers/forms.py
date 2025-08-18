"""
Forms for farmer management functionality.
"""
from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

from .models import Farmer
from regions.models import Region

User = get_user_model()


class FarmerRegistrationForm(forms.Form):
    """Form for registering new farmers"""
    
    # User fields
    first_name = forms.CharField(
        max_length=30,
        label=_('First Name'),
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': _('Enter first name')
        })
    )
    
    last_name = forms.CharField(
        max_length=30,
        label=_('Last Name'),
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': _('Enter last name')
        })
    )
    
    email = forms.EmailField(
        label=_('Email'),
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': _('Enter email address')
        })
    )
    
    password = forms.CharField(
        label=_('Password'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': _('Enter password')
        })
    )
    
    # Farmer fields
    contact_number = forms.CharField(
        max_length=15,
        label=_('Contact Number'),
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': _('Enter contact number')
        })
    )
    
    region = forms.ModelChoiceField(
        queryset=Region.objects.filter(is_active=True),
        label=_('Region'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    farm_size = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0,
        label=_('Farm Size (Acres)'),
        widget=forms.NumberInput(attrs={
            'class': 'form-input',
            'placeholder': _('Enter farm size in acres')
        })
    )
    
    farm_type = forms.CharField(
        max_length=50,
        label=_('Farm Type'),
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': _('e.g., Vegetable farming, Fruit farming')
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Limit region choices for buyer_head users
        if self.user and self.user.role == 'buyer_head':
            self.fields['region'].queryset = Region.objects.filter(id=self.user.region.id)
            self.fields['region'].initial = self.user.region
    
    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise ValidationError(_('A user with this email already exists.'))
        return email
    
    def save(self):
        """Create user and farmer objects"""
        # Create user
        user = User.objects.create_user(
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
            role='farmer',
            region=self.cleaned_data['region']
        )
        
        # Create farmer profile
        farmer = Farmer.objects.create(
            user=user,
            contact_number=self.cleaned_data['contact_number'],
            region=self.cleaned_data['region'],
            farm_size=self.cleaned_data['farm_size'],
            farm_type=self.cleaned_data['farm_type'],
        )
        
        return farmer


class FarmerProfileForm(forms.ModelForm):
    """Form for editing farmer profiles"""
    
    class Meta:
        model = Farmer
        fields = [
            'contact_number', 'region', 'farm_size', 'farm_type',
            'bank_account_number', 'bank_ifsc', 'bank_name', 'is_active'
        ]
        widgets = {
            'contact_number': forms.TextInput(attrs={'class': 'form-input'}),
            'region': forms.Select(attrs={'class': 'form-select'}),
            'farm_size': forms.NumberInput(attrs={'class': 'form-input'}),
            'farm_type': forms.TextInput(attrs={'class': 'form-input'}),
            'bank_account_number': forms.TextInput(attrs={'class': 'form-input'}),
            'bank_ifsc': forms.TextInput(attrs={'class': 'form-input'}),
            'bank_name': forms.TextInput(attrs={'class': 'form-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }
        labels = {
            'contact_number': _('Contact Number'),
            'region': _('Region'),
            'farm_size': _('Farm Size (Acres)'),
            'farm_type': _('Farm Type'),
            'bank_account_number': _('Bank Account Number'),
            'bank_ifsc': _('Bank IFSC Code'),
            'bank_name': _('Bank Name'),
            'is_active': _('Active'),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.is_self_edit = kwargs.pop('is_self_edit', False)
        super().__init__(*args, **kwargs)
        
        # Limit region choices for buyer_head users
        if self.user and self.user.role == 'buyer_head':
            self.fields['region'].queryset = Region.objects.filter(id=self.user.region.id)
        
        # Remove sensitive fields for farmer self-editing
        if self.is_self_edit:
            del self.fields['is_active']
            del self.fields['region']  # Farmers can't change their region
