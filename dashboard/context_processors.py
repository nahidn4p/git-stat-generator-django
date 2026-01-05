"""
Context processors for dashboard app.
"""
from django.conf import settings
from .themes import get_theme, get_all_themes, DEFAULT_THEME


def theme_context(request):
    """Add theme information to template context."""
    # Get theme from query parameter or cookie
    theme_id = request.GET.get('theme') or request.COOKIES.get('theme', DEFAULT_THEME)
    
    # Validate theme exists
    theme = get_theme(theme_id)
    
    return {
        'current_theme': theme,
        'all_themes': get_all_themes(),
        'theme_id': theme.id,
    }

