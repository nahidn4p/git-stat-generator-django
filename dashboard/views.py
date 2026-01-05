"""
Views for the dashboard app.
"""
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_http_methods
from .services.github_client import GitHubClient, GitHubStats
from .themes import get_theme, get_all_themes, DEFAULT_THEME
import json


def home_view(request):
    """Landing page with username search form."""
    theme_id = request.COOKIES.get('theme', DEFAULT_THEME)
    theme = get_theme(theme_id)
    context = {
        'theme': theme,
        'theme_id': theme_id,
        'all_themes': get_all_themes(),
    }
    return render(request, 'dashboard/home.html', context)


def stats_view(request, username):
    """
    Main stats dashboard view.
    Fetches GitHub stats and renders the dashboard.
    """
    # Get theme from query parameter or cookie
    theme_id = request.GET.get('theme') or request.COOKIES.get('theme', DEFAULT_THEME)
    theme = get_theme(theme_id)
    
    try:
        client = GitHubClient()
        stats = client.get_user_stats(username)
        
        # Serialize data for JavaScript charts
        daily_contributions_json = json.dumps(stats.daily_contributions)
        monthly_contributions_json = json.dumps(stats.monthly_contributions)
        
        context = {
            'stats': stats,
            'theme': theme,
            'theme_id': theme_id,
            'daily_contributions_json': daily_contributions_json,
            'monthly_contributions_json': monthly_contributions_json,
            'all_themes': get_all_themes(),
        }
        
        response = render(request, 'dashboard/stats.html', context)
        
        # Set theme cookie if provided in query
        if request.GET.get('theme'):
            response.set_cookie('theme', theme_id, max_age=365*24*60*60)  # 1 year
        
        return response
        
    except ValueError as e:
        error_message = str(e)
        is_rate_limit = 'RATE_LIMIT' in error_message
        has_token = 'RATE_LIMIT_WITH_TOKEN' in error_message
        no_token = 'RATE_LIMIT_NO_TOKEN' in error_message
        
        # Clean up error message for display
        display_error = error_message.replace(' RATE_LIMIT_NO_TOKEN', '').replace(' RATE_LIMIT_WITH_TOKEN', '')
        
        context = {
            'error': display_error,
            'username': username,
            'theme': theme,
            'theme_id': theme_id,
            'all_themes': get_all_themes(),
            'is_rate_limit': is_rate_limit,
            'has_token': has_token,
            'no_token': no_token,
        }
        status_code = 429 if is_rate_limit else 404
        return render(request, 'dashboard/error.html', context, status=status_code)
    except Exception as e:
        error_message = f"An unexpected error occurred: {str(e)}"
        context = {
            'error': error_message,
            'username': username,
            'theme': theme,
            'theme_id': theme_id,
            'all_themes': get_all_themes(),
        }
        return render(request, 'dashboard/error.html', context, status=500)


@require_http_methods(["POST"])
def set_theme_view(request):
    """Set theme cookie and redirect back."""
    theme_id = request.POST.get('theme', DEFAULT_THEME)
    redirect_url = request.POST.get('redirect', '/')
    
    response = redirect(redirect_url)
    response.set_cookie('theme', theme_id, max_age=365*24*60*60)  # 1 year
    return response


def badge_view(request, username):
    """
    Generate SVG badge with GitHub stats.
    Supports theme parameter via query string.
    """
    theme_id = request.GET.get('theme', DEFAULT_THEME)
    theme = get_theme(theme_id)
    
    try:
        client = GitHubClient()
        stats = client.get_user_stats(username)
        
        # Generate SVG
        svg = generate_badge_svg(stats, theme)
        
        response = HttpResponse(svg, content_type='image/svg+xml')
        response['Cache-Control'] = 'public, max-age=3600'  # Cache for 1 hour
        return response
        
    except ValueError as e:
        # Return error SVG
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="400" height="100">
            <rect width="400" height="100" fill="#1a1a1a"/>
            <text x="200" y="50" font-family="Arial" font-size="14" fill="#ff6b6b" text-anchor="middle">
                Error: {str(e)[:50]}
            </text>
        </svg>'''
        return HttpResponse(svg, content_type='image/svg+xml', status=404)
    except Exception as e:
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="400" height="100">
            <rect width="400" height="100" fill="#1a1a1a"/>
            <text x="200" y="50" font-family="Arial" font-size="14" fill="#ff6b6b" text-anchor="middle">
                Error loading stats
            </text>
        </svg>'''
        return HttpResponse(svg, content_type='image/svg+xml', status=500)


def generate_badge_svg(stats: GitHubStats, theme) -> str:
    """Generate enhanced SVG badge with comprehensive GitHub stats."""
    # Map theme IDs to background colors
    bg_colors = {
        'neon_dark': '#141b2d',
        'solar_dark': '#1f2937',
        'light_clean': '#ffffff',
        'minimal_dark': '#111827',
    }
    bg_color = bg_colors.get(theme.id, '#141b2d')
    bg_color_light = bg_colors.get(theme.id, '#1a2332')
    
    # Map theme IDs to text colors
    text_colors = {
        'neon_dark': '#e5e7eb',
        'solar_dark': '#e5e7eb',
        'light_clean': '#111827',
        'minimal_dark': '#e5e7eb',
    }
    text_color = text_colors.get(theme.id, '#e5e7eb')
    text_color_secondary = '#9ca3af' if theme.id != 'light_clean' else '#6b7280'
    
    accent = theme.accent_color
    accent_light = theme.accent_color_light
    
    # Calculate rating
    rating = "C+"
    if stats.total_stars > 100:
        rating = "B+"
    if stats.total_stars > 500:
        rating = "A"
    if stats.total_stars > 1000:
        rating = "A+"
    
    # Get top language
    top_language = stats.languages[0]['name'] if stats.languages else 'N/A'
    
    # Format large numbers
    def format_number(num):
        if num >= 1000:
            return f"{num/1000:.1f}k"
        return str(num)
    
    # Badge dimensions
    width = 600
    height = 320
    
    # GitHub logo SVG path (GitHub mark - simplified version)
    github_logo_path = "M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.012 8.012 0 0 0 16 8c0-4.42-3.58-8-8-8z"
    
    svg_content = f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{width}" height="{height}">
        <defs>
            <linearGradient id="bgGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style="stop-color:{bg_color};stop-opacity:1" />
                <stop offset="100%" style="stop-color:{bg_color_light};stop-opacity:1" />
            </linearGradient>
            <linearGradient id="accentGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style="stop-color:{accent};stop-opacity:1" />
                <stop offset="100%" style="stop-color:{accent_light};stop-opacity:1" />
            </linearGradient>
            <filter id="glow">
                <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
                <feMerge>
                    <feMergeNode in="coloredBlur"/>
                    <feMergeNode in="SourceGraphic"/>
                </feMerge>
            </filter>
        </defs>
        
        <!-- Background -->
        <rect width="{width}" height="{height}" fill="url(#bgGradient)" rx="12"/>
        
        <!-- Header Section -->
        <rect width="{width}" height="80" fill="url(#accentGradient)" opacity="0.15" rx="12"/>
        
        <!-- GitHub Logo with Link -->
        <a xlink:href="https://github.com/{stats.username}" target="_blank">
            <g transform="translate(30, 20)">
                <!-- GitHub logo background -->
                <rect x="0" y="0" width="40" height="40" rx="8" fill="rgba(255, 255, 255, 0.1)" stroke="{accent}" stroke-width="1.5"/>
                <!-- GitHub logo icon -->
                <g transform="translate(8, 8) scale(0.24)">
                    <path d="{github_logo_path}" fill="{accent}"/>
                </g>
            </g>
            <!-- Hover effect -->
            <title>View {stats.username} on GitHub</title>
        </a>
        
        <!-- Username with GitHub link -->
        <a xlink:href="https://github.com/{stats.username}" target="_blank" style="text-decoration: none;">
            <text x="75" y="35" font-family="Inter, system-ui, sans-serif" font-size="24" font-weight="700" fill="{accent}">
                {stats.username}
            </text>
        </a>
        <text x="75" y="60" font-family="Inter, system-ui, sans-serif" font-size="14" fill="{text_color_secondary}">
            {stats.name[:40] if len(stats.name) > 40 else stats.name}
        </text>
        
        <!-- GitHub Stats Label -->
        <text x="75" y="78" font-family="Inter, system-ui, sans-serif" font-size="10" fill="{text_color_secondary}" opacity="0.7">
            GitHub Statistics
        </text>
        
        <!-- Rating Badge -->
        <circle cx="{width-50}" cy="40" r="30" fill="url(#accentGradient)" opacity="0.2"/>
        <circle cx="{width-50}" cy="40" r="24" fill="{bg_color}" stroke="{accent}" stroke-width="2"/>
        <text x="{width-50}" y="47" font-family="Inter, system-ui, sans-serif" font-size="18" font-weight="700" fill="{accent}" text-anchor="middle">
            {rating}
        </text>
        <text x="{width-50}" y="62" font-family="Inter, system-ui, sans-serif" font-size="10" fill="{text_color_secondary}" text-anchor="middle">
            Rating
        </text>
        
        <!-- Stats Grid -->
        <!-- Row 1 -->
        <g transform="translate(30, 100)">
            <!-- Stars -->
            <rect x="0" y="0" width="120" height="50" rx="8" fill="rgba(255, 255, 255, 0.05)" stroke="rgba(255, 255, 255, 0.1)" stroke-width="1"/>
            <text x="15" y="20" font-family="Inter, system-ui, sans-serif" font-size="11" fill="{text_color_secondary}">Stars</text>
            <text x="15" y="38" font-family="Inter, system-ui, sans-serif" font-size="18" font-weight="700" fill="{accent}">{format_number(stats.total_stars)}</text>
            
            <!-- Repositories -->
            <rect x="140" y="0" width="120" height="50" rx="8" fill="rgba(255, 255, 255, 0.05)" stroke="rgba(255, 255, 255, 0.1)" stroke-width="1"/>
            <text x="155" y="20" font-family="Inter, system-ui, sans-serif" font-size="11" fill="{text_color_secondary}">Repositories</text>
            <text x="155" y="38" font-family="Inter, system-ui, sans-serif" font-size="18" font-weight="700" fill="{accent}">{stats.public_repos}</text>
            
            <!-- Followers -->
            <rect x="280" y="0" width="120" height="50" rx="8" fill="rgba(255, 255, 255, 0.05)" stroke="rgba(255, 255, 255, 0.1)" stroke-width="1"/>
            <text x="295" y="20" font-family="Inter, system-ui, sans-serif" font-size="11" fill="{text_color_secondary}">Followers</text>
            <text x="295" y="38" font-family="Inter, system-ui, sans-serif" font-size="18" font-weight="700" fill="{accent}">{format_number(stats.followers)}</text>
            
            <!-- Contributions -->
            <rect x="420" y="0" width="120" height="50" rx="8" fill="rgba(255, 255, 255, 0.05)" stroke="rgba(255, 255, 255, 0.1)" stroke-width="1"/>
            <text x="435" y="20" font-family="Inter, system-ui, sans-serif" font-size="11" fill="{text_color_secondary}">Contributions</text>
            <text x="435" y="38" font-family="Inter, system-ui, sans-serif" font-size="18" font-weight="700" fill="{accent}">{format_number(stats.total_contributions)}</text>
        </g>
        
        <!-- Row 2 -->
        <g transform="translate(30, 170)">
            <!-- Commits -->
            <rect x="0" y="0" width="120" height="50" rx="8" fill="rgba(255, 255, 255, 0.05)" stroke="rgba(255, 255, 255, 0.1)" stroke-width="1"/>
            <text x="15" y="20" font-family="Inter, system-ui, sans-serif" font-size="11" fill="{text_color_secondary}">Commits (1Y)</text>
            <text x="15" y="38" font-family="Inter, system-ui, sans-serif" font-size="18" font-weight="700" fill="{accent}">{format_number(stats.commits_last_year)}</text>
            
            <!-- Pull Requests -->
            <rect x="140" y="0" width="120" height="50" rx="8" fill="rgba(255, 255, 255, 0.05)" stroke="rgba(255, 255, 255, 0.1)" stroke-width="1"/>
            <text x="155" y="20" font-family="Inter, system-ui, sans-serif" font-size="11" fill="{text_color_secondary}">Pull Requests</text>
            <text x="155" y="38" font-family="Inter, system-ui, sans-serif" font-size="18" font-weight="700" fill="{accent}">{stats.pull_requests_last_year}</text>
            
            <!-- Current Streak -->
            <rect x="280" y="0" width="120" height="50" rx="8" fill="rgba(255, 255, 255, 0.05)" stroke="rgba(255, 255, 255, 0.1)" stroke-width="1"/>
            <text x="295" y="20" font-family="Inter, system-ui, sans-serif" font-size="11" fill="{text_color_secondary}">Current Streak</text>
            <text x="295" y="38" font-family="Inter, system-ui, sans-serif" font-size="18" font-weight="700" fill="{accent}">{stats.current_streak} 🔥</text>
            
            <!-- Top Language -->
            <rect x="420" y="0" width="120" height="50" rx="8" fill="rgba(255, 255, 255, 0.05)" stroke="rgba(255, 255, 255, 0.1)" stroke-width="1"/>
            <text x="435" y="20" font-family="Inter, system-ui, sans-serif" font-size="11" fill="{text_color_secondary}">Top Language</text>
            <text x="435" y="38" font-family="Inter, system-ui, sans-serif" font-size="16" font-weight="700" fill="{accent}">{top_language[:12]}</text>
        </g>
        
        <!-- Footer with contribution indicator -->
        <g transform="translate(30, 250)">
            <text x="0" y="15" font-family="Inter, system-ui, sans-serif" font-size="11" fill="{text_color_secondary}">Contributed to {stats.contributed_to} repositories</text>
            <!-- Contribution bar -->
            <rect x="0" y="25" width="540" height="8" rx="4" fill="rgba(255, 255, 255, 0.1)"/>
            <rect x="0" y="25" width="{min(540, (stats.contributed_to / max(stats.public_repos, 1)) * 540)}" height="8" rx="4" fill="url(#accentGradient)"/>
        </g>
        
        <!-- Decorative elements -->
        <circle cx="50" cy="280" r="20" fill="{accent}" opacity="0.1"/>
        <circle cx="{width-50}" cy="280" r="20" fill="{accent}" opacity="0.1"/>
    </svg>'''
    
    return svg_content

