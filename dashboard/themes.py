"""
Theme definitions for the GitHub stats dashboard.
"""
from typing import Dict, List


class Theme:
    """Theme configuration."""
    
    def __init__(
        self,
        id: str,
        name: str,
        body_classes: str,
        card_classes: str,
        text_primary: str,
        text_secondary: str,
        accent_color: str,
        accent_color_light: str,
        success_color: str,
        warning_color: str,
        chart_line_color: str,
        chart_fill_color: str,
    ):
        self.id = id
        self.name = name
        self.body_classes = body_classes
        self.card_classes = card_classes
        self.text_primary = text_primary
        self.text_secondary = text_secondary
        self.accent_color = accent_color
        self.accent_color_light = accent_color_light
        self.success_color = success_color
        self.warning_color = warning_color
        self.chart_line_color = chart_line_color
        self.chart_fill_color = chart_fill_color


# Theme registry
THEMES: Dict[str, Theme] = {
    'neon_dark': Theme(
        id='neon_dark',
        name='Neon Dark',
        body_classes='theme-neon-dark bg-dark-bg',
        card_classes='bg-dark-card border border-gray-700',
        text_primary='text-gray-100',
        text_secondary='text-gray-400',
        accent_color='#00d4ff',
        accent_color_light='#33dfff',
        success_color='#10b981',
        warning_color='#f59e0b',
        chart_line_color='#00d4ff',
        chart_fill_color='rgba(0, 212, 255, 0.1)',
    ),
    'solar_dark': Theme(
        id='solar_dark',
        name='Solar Dark',
        body_classes='theme-solar-dark bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900',
        card_classes='bg-gray-800 border border-gray-700',
        text_primary='text-gray-100',
        text_secondary='text-gray-400',
        accent_color='#fdb44b',
        accent_color_light='#fdc66b',
        success_color='#10b981',
        warning_color='#ff6b6b',
        chart_line_color='#fdb44b',
        chart_fill_color='rgba(253, 180, 75, 0.1)',
    ),
    'light_clean': Theme(
        id='light_clean',
        name='Light Clean',
        body_classes='theme-light-clean bg-gray-50',
        card_classes='bg-white border border-gray-200',
        text_primary='text-gray-900',
        text_secondary='text-gray-600',
        accent_color='#3b82f6',
        accent_color_light='#60a5fa',
        success_color='#10b981',
        warning_color='#f59e0b',
        chart_line_color='#3b82f6',
        chart_fill_color='rgba(59, 130, 246, 0.1)',
    ),
    'minimal_dark': Theme(
        id='minimal_dark',
        name='Minimal Dark',
        body_classes='theme-minimal-dark bg-gray-950',
        card_classes='bg-gray-900 border border-gray-800',
        text_primary='text-gray-100',
        text_secondary='text-gray-500',
        accent_color='#8b5cf6',
        accent_color_light='#a78bfa',
        success_color='#10b981',
        warning_color='#f59e0b',
        chart_line_color='#8b5cf6',
        chart_fill_color='rgba(139, 92, 246, 0.1)',
    ),
}

DEFAULT_THEME = 'neon_dark'


def get_theme(theme_id: str) -> Theme:
    """Get a theme by ID, returning default if not found."""
    return THEMES.get(theme_id, THEMES[DEFAULT_THEME])


def get_all_themes() -> List[Theme]:
    """Get all available themes."""
    return list(THEMES.values())


def get_theme_names() -> List[tuple]:
    """Get list of (id, name) tuples for theme selection."""
    return [(theme.id, theme.name) for theme in THEMES.values()]

