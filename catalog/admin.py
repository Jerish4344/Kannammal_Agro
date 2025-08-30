from django.contrib import admin
from .models import SKU, SKUImage


class SKUImageInline(admin.TabularInline):
    model = SKUImage
    extra = 1
    fields = ('image', 'caption', 'is_primary')


@admin.register(SKU)
class SKUAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'category', 'unit', 'is_active', 'created_at')
    list_filter = ('category', 'unit', 'is_active', 'created_at')
    search_fields = ('name', 'code', 'description')
    ordering = ('category', 'name')
    inlines = [SKUImageInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'code', 'category'),
        }),
        ('Localization', {
            'fields': ('name_ta', 'name_hi'),
        }),
        ('Product Details', {
            'fields': ('description', 'unit', 'image', 'min_order_quantity'),
        }),
        ('Status', {
            'fields': ('is_active',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')


@admin.register(SKUImage)
class SKUImageAdmin(admin.ModelAdmin):
    list_display = ('sku', 'caption', 'is_primary', 'created_at')
    list_filter = ('is_primary', 'created_at')
    search_fields = ('sku__name', 'caption')
    ordering = ('sku', '-is_primary', 'created_at')
    
    fieldsets = (
        ('Image Information', {
            'fields': ('sku', 'image', 'caption', 'is_primary'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
