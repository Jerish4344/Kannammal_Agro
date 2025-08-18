"""Language template tags for internationalization."""

from django import template
from django.conf import settings
from django.utils import translation

register = template.Library()


@register.simple_tag
def get_current_language():
    """Get the current active language code."""
    return translation.get_language()


@register.simple_tag
def get_current_language_name():
    """Get the current active language name."""
    current_lang = translation.get_language()
    for code, name in settings.LANGUAGES:
        if code == current_lang:
            return name
    return 'English'  # Default fallback


@register.simple_tag
def get_available_languages():
    """Get all available languages."""
    return settings.LANGUAGES


@register.filter
def currency_format(value):
    """Format currency with ₹ symbol."""
    if value is None:
        return '₹ 0'
    try:
        return f'₹ {float(value):,.2f}'
    except (ValueError, TypeError):
        return '₹ 0'


@register.inclusion_tag('partials/language_switcher.html', takes_context=True)
def language_switcher(context):
    """Render language switcher component."""
    request = context['request']
    return {
        'current_language': translation.get_language(),
        'available_languages': settings.LANGUAGES,
        'request': request,
    }
