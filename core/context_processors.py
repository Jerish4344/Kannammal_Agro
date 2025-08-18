"""Context processors for core functionality."""

from django.conf import settings


def feature_flags(request):
    """Add feature flags to template context."""
    return {
        'FEATURE_VOICE_INPUT': getattr(settings, 'FEATURE_VOICE_INPUT', False),
        'FEATURE_RANKING': getattr(settings, 'FEATURE_RANKING', False),
    }
