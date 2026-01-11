"""
Views for the dashboard app.
"""
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_http_methods
from django.utils.html import escape
from django.core.cache import cache
from .services.github_client import GitHubClient, GitHubStats
from .themes import get_theme, get_all_themes, DEFAULT_THEME
import json
import requests
import base64


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
    Generate modern SVG badge with GitHub stats.
    Supports theme parameter via query string.
    """
    theme_id = request.GET.get('theme', DEFAULT_THEME)
    theme = get_theme(theme_id)
    
    try:
        client = GitHubClient()
        stats = client.get_user_stats(username)
        
        # Generate modern SVG badge
        svg = generate_badge_svg(stats, theme)
        
        response = HttpResponse(svg, content_type='image/svg+xml')
        response['Cache-Control'] = 'public, max-age=3600'  # Cache for 1 hour
        return response
        
    except ValueError as e:
        # Return error SVG
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="400" height="100">
            <defs>
                <linearGradient id="errorGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" style="stop-color:#ff6b6b;stop-opacity:1" />
                    <stop offset="100%" style="stop-color:#ee5a6f;stop-opacity:1" />
                </linearGradient>
            </defs>
            <rect width="400" height="100" fill="url(#errorGrad)" rx="12"/>
            <text x="200" y="50" font-family="Inter, system-ui, sans-serif" font-size="14" fill="#fff" text-anchor="middle" font-weight="600">
                Error: {escape(str(e)[:50])}
            </text>
        </svg>'''
        return HttpResponse(svg, content_type='image/svg+xml', status=404)
    except Exception as e:
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="400" height="100">
            <defs>
                <linearGradient id="errorGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" style="stop-color:#ff6b6b;stop-opacity:1" />
                    <stop offset="100%" style="stop-color:#ee5a6f;stop-opacity:1" />
                </linearGradient>
            </defs>
            <rect width="400" height="100" fill="url(#errorGrad)" rx="12"/>
            <text x="200" y="50" font-family="Inter, system-ui, sans-serif" font-size="14" fill="#fff" text-anchor="middle" font-weight="600">
                Error loading stats
            </text>
        </svg>'''
        return HttpResponse(svg, content_type='image/svg+xml', status=500)


def get_avatar_base64(avatar_url: str) -> str:
    """Fetch avatar image and convert to base64 data URI to avoid CORS issues."""
    cache_key = f"avatar_base64_{avatar_url}"
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    try:
        # Fetch the image
        response = requests.get(avatar_url, timeout=5, headers={
            'User-Agent': 'GitHub-Stats-Generator/1.0'
        })
        response.raise_for_status()
        
        # Determine content type
        content_type = response.headers.get('Content-Type', 'image/png')
        if 'image' not in content_type:
            content_type = 'image/png'
        
        # Encode to base64
        image_data = base64.b64encode(response.content).decode('utf-8')
        data_uri = f"data:{content_type};base64,{image_data}"
        
        # Cache for 1 hour
        cache.set(cache_key, data_uri, 3600)
        return data_uri
    except Exception as e:
        # Return None to use fallback
        print(f"Error fetching avatar: {e}")
        return None


def generate_badge_svg(stats: GitHubStats, theme) -> str:
    """Generate modern, colorful SVG badge with comprehensive GitHub stats."""
    
    # Escape user input for security
    safe_username = escape(stats.username)
    safe_name = escape(stats.name[:40] if stats.name and len(stats.name) > 40 else (stats.name or safe_username))
    
    # Get theme colors
    accent_color = theme.accent_color
    accent_color_light = theme.accent_color_light
    
    # Convert Tailwind text color classes to hex
    def convert_tailwind_color(tailwind_class):
        """Convert Tailwind color class to hex value."""
        if not tailwind_class.startswith('text-'):
            return tailwind_class  # Already a hex color
        
        # Tailwind gray scale mapping
        gray_map = {
            'gray-50': '#f9fafb',
            'gray-100': '#f3f4f6',
            'gray-200': '#e5e7eb',
            'gray-300': '#d1d5db',
            'gray-400': '#9ca3af',
            'gray-500': '#6b7280',
            'gray-600': '#4b5563',
            'gray-700': '#374151',
            'gray-800': '#1f2937',
            'gray-900': '#111827',
            'gray-950': '#030712',
        }
        
        color_class = tailwind_class.replace('text-', '')
        return gray_map.get(color_class, '#ffffff')
    
    text_primary = convert_tailwind_color(theme.text_primary)
    text_secondary = convert_tailwind_color(theme.text_secondary)
    
    # Determine if theme is light or dark
    is_light_theme = theme.id == 'light_clean'
    
    # Theme-dependent background colors
    if is_light_theme:
        bg_color = '#ffffff'
        bg_overlay_opacity = '0.1'
        header_bg = '#f9fafb'
        header_overlay_opacity = '0.2'
        card_bg = '#ffffff'
        card_text_secondary = '#6b7280'
        decorative_circle_fill = 'rgba(0,0,0,0.05)'
        avatar_bg = 'rgba(0,0,0,0.05)'
        avatar_stroke = 'rgba(0,0,0,0.1)'
        rating_bg = 'rgba(0,0,0,0.1)'
        footer_bg = '#f9fafb'
        footer_overlay_opacity = '0.2'
        username_fill = '#111827'
        name_fill = 'rgba(17,24,39,0.8)'
        rating_label_fill = 'rgba(17,24,39,0.7)'
        github_logo_fill = '#24292f'
    else:
        bg_color = '#0a0e27'
        bg_overlay_opacity = '0.3'
        header_bg = '#141b2d'
        header_overlay_opacity = '0.4'
        card_bg = '#1a2332'
        card_text_secondary = '#9ca3af'
        decorative_circle_fill = 'rgba(0,0,0,0.3)'
        avatar_bg = 'rgba(255,255,255,0.15)'
        avatar_stroke = 'rgba(255,255,255,0.3)'
        rating_bg = 'rgba(0,0,0,0.4)'
        footer_bg = '#141b2d'
        footer_overlay_opacity = '0.3'
        username_fill = '#ffffff'
        name_fill = 'rgba(255,255,255,0.8)'
        rating_label_fill = 'rgba(255,255,255,0.7)'
        github_logo_fill = '#ffffff'
    
    # Calculate comprehensive rating based on multiple metrics
    def calculate_rating(stats):
        """Calculate rating based on multiple GitHub metrics with weighted scoring."""
        score = 0
        
        # Stars: 0-35 points (max at 1500+ stars) - Most visible metric
        stars_score = min(35, (stats.total_stars / 1500) * 35)
        score += stars_score
        
        # Contributions: 0-25 points (max at 4000+ contributions) - Shows activity
        contributions_score = min(25, (stats.total_contributions / 4000) * 25)
        score += contributions_score
        
        # Commits: 0-20 points (max at 1500+ commits/year) - Development activity
        commits_score = min(20, (stats.commits_last_year / 1500) * 20)
        score += commits_score
        
        # Pull Requests: 0-12 points (max at 150+ PRs/year) - Collaboration
        prs_score = min(12, (stats.pull_requests_last_year / 150) * 12)
        score += prs_score
        
        # Repositories: 0-8 points (max at 80+ repos) - Project diversity
        repos_score = min(8, (stats.public_repos / 80) * 8)
        score += repos_score
        
        # Determine rating based on total score (out of 100)
        if score >= 75:
            return "A+", "#8b5cf6"
        elif score >= 55:
            return "A", "#3b82f6"
        elif score >= 35:
            return "B+", "#10b981"
        else:
            return "C+", "#f59e0b"
    
    rating, rating_color = calculate_rating(stats)
    
    # Get avatar as base64 to avoid CORS issues (after all theme colors are defined)
    avatar_data_uri = get_avatar_base64(stats.avatar_url)
    
    # Build avatar image tag with proper circular clipping
    if avatar_data_uri:
        avatar_image_tag = f'<image href="{avatar_data_uri}" x="25" y="15" width="70" height="70" clip-path="url(#avatarClip)" preserveAspectRatio="xMidYMid cover"/>'
    else:
        # Fallback to initials if image fails to load
        initial = safe_username[0].upper() if safe_username else "?"
        avatar_image_tag = f'<circle cx="60" cy="50" r="30" fill="{accent_color}" opacity="0.3"/><text x="60" y="55" font-family="Inter, system-ui, sans-serif" font-size="24" font-weight="700" fill="{username_fill}" text-anchor="middle">{initial}</text>'
    
    # Get top language
    top_language = escape(stats.languages[0]['name'][:12]) if stats.languages else 'N/A'
    top_language_full = stats.languages[0]['name'] if stats.languages else 'N/A'
    
    # Language icon/abbreviation mapping
    def get_language_icon(lang_name):
        """Get a simple icon representation for a language."""
        if not lang_name or lang_name == 'N/A':
            return '?', ''
        
        lang_lower = lang_name.lower()
        # Common language abbreviations
        lang_icons = {
            'python': 'Py',
            'javascript': 'JS',
            'typescript': 'TS',
            'java': 'J',
            'c++': 'C+',
            'c#': 'C#',
            'go': 'Go',
            'rust': 'Rs',
            'php': 'PHP',
            'ruby': 'Rb',
            'swift': 'Sw',
            'kotlin': 'Kt',
            'dart': 'Dt',
            'html': 'H',
            'css': 'C',
            'scss': 'S',
            'shell': 'Sh',
            'bash': 'B',
            'powershell': 'PS',
            'sql': 'SQL',
            'r': 'R',
            'matlab': 'M',
            'scala': 'Sc',
            'perl': 'Pl',
        }
        
        # Check for exact match or partial match
        for key, icon in lang_icons.items():
            if key in lang_lower or lang_lower in key:
                return icon, ''
        
        # Default: use first 2-3 letters
        if len(lang_name) >= 3:
            return lang_name[:3].upper(), ''
        return lang_name[0].upper(), ''
    
    lang_icon_text, lang_icon_path = get_language_icon(top_language_full)
    
    # Format large numbers
    def format_number(num):
        if num >= 1000000:
            return f"{num/1000000:.1f}M"
        if num >= 1000:
            return f"{num/1000:.1f}k"
        return str(num)
    
    # Badge dimensions
    width = 700
    height = 380
    
    # Colorful gradients for stat cards (keep colorful as per user preference)
    stat_gradients = [
        ("#667eea", "#764ba2"),  # Stars - Purple
        ("#f093fb", "#f5576c"),  # Repos - Pink
        ("#4facfe", "#00f2fe"),  # Followers - Blue
        ("#43e97b", "#38f9d7"),  # Contributions - Green
        ("#fa709a", "#fee140"),  # Commits - Yellow-Pink
        ("#30cfd0", "#330867"),  # PRs - Cyan-Purple
        ("#ff6b6b", "#ee5a6f"),  # Streak - Red
        ("#a8edea", "#fed6e3"),  # Language - Light
    ]
    
    # GitHub logo SVG path (GitHub mark)
    github_logo_path = "M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.012 8.012 0 0 0 16 8c0-4.42-3.58-8-8-8z"
    
    svg_content = f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{width}" height="{height}">
        <defs>
            <!-- Animated background gradient using theme colors -->
            <linearGradient id="bgGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style="stop-color:{accent_color};stop-opacity:1">
                    <animate attributeName="stop-color" values="{accent_color};{accent_color_light};{accent_color};{accent_color}" dur="15s" repeatCount="indefinite"/>
                </stop>
                <stop offset="50%" style="stop-color:{accent_color_light};stop-opacity:1">
                    <animate attributeName="stop-color" values="{accent_color_light};{accent_color};{accent_color_light};{accent_color_light}" dur="15s" repeatCount="indefinite"/>
                </stop>
                <stop offset="100%" style="stop-color:{accent_color};stop-opacity:0.8">
                    <animate attributeName="stop-color" values="{accent_color};{accent_color_light};{accent_color};{accent_color}" dur="15s" repeatCount="indefinite"/>
                </stop>
            </linearGradient>
            
            <!-- Header gradient using theme colors -->
            <linearGradient id="headerGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style="stop-color:{accent_color};stop-opacity:1" />
                <stop offset="100%" style="stop-color:{accent_color_light};stop-opacity:1" />
            </linearGradient>
            
            <!-- Rating gradient -->
            <linearGradient id="ratingGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style="stop-color:{rating_color};stop-opacity:1" />
                <stop offset="100%" style="stop-color:{rating_color};stop-opacity:0.7" />
            </linearGradient>
            
            <!-- Glow filter -->
            <filter id="glow">
                <feGaussianBlur stdDeviation="4" result="coloredBlur"/>
                <feMerge>
                    <feMergeNode in="coloredBlur"/>
                    <feMergeNode in="SourceGraphic"/>
                </feMerge>
            </filter>
            
            <!-- Shadow filter -->
            <filter id="shadow" x="-50%" y="-50%" width="200%" height="200%">
                <feDropShadow dx="0" dy="4" stdDeviation="8" flood-opacity="0.3"/>
            </filter>
            
            <!-- Stat card gradients -->
            <linearGradient id="statGrad1" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style="stop-color:{stat_gradients[0][0]};stop-opacity:1" />
                <stop offset="100%" style="stop-color:{stat_gradients[0][1]};stop-opacity:1" />
            </linearGradient>
            <linearGradient id="statGrad2" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style="stop-color:{stat_gradients[1][0]};stop-opacity:1" />
                <stop offset="100%" style="stop-color:{stat_gradients[1][1]};stop-opacity:1" />
            </linearGradient>
            <linearGradient id="statGrad3" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style="stop-color:{stat_gradients[2][0]};stop-opacity:1" />
                <stop offset="100%" style="stop-color:{stat_gradients[2][1]};stop-opacity:1" />
            </linearGradient>
            <linearGradient id="statGrad4" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style="stop-color:{stat_gradients[3][0]};stop-opacity:1" />
                <stop offset="100%" style="stop-color:{stat_gradients[3][1]};stop-opacity:1" />
            </linearGradient>
            <linearGradient id="statGrad5" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style="stop-color:{stat_gradients[4][0]};stop-opacity:1" />
                <stop offset="100%" style="stop-color:{stat_gradients[4][1]};stop-opacity:1" />
            </linearGradient>
            <linearGradient id="statGrad6" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style="stop-color:{stat_gradients[5][0]};stop-opacity:1" />
                <stop offset="100%" style="stop-color:{stat_gradients[5][1]};stop-opacity:1" />
            </linearGradient>
            <linearGradient id="statGrad7" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style="stop-color:{stat_gradients[6][0]};stop-opacity:1" />
                <stop offset="100%" style="stop-color:{stat_gradients[6][1]};stop-opacity:1" />
            </linearGradient>
            <linearGradient id="statGrad8" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style="stop-color:{stat_gradients[7][0]};stop-opacity:1" />
                <stop offset="100%" style="stop-color:{stat_gradients[7][1]};stop-opacity:1" />
            </linearGradient>
            
            <!-- Animated rotating circle for header -->
            <circle id="rotatingCircle" r="200" fill="rgba(255,255,255,0.1)">
                <animateTransform attributeName="transform" type="rotate" values="0 350 90;360 350 90" dur="20s" repeatCount="indefinite"/>
            </circle>
            
            <!-- Circular clip path for avatar -->
            <clipPath id="avatarClip">
                <circle cx="60" cy="50" r="35"/>
            </clipPath>
        </defs>
        
        <!-- Theme-dependent background with animated gradient -->
        <rect width="{width}" height="{height}" fill="{bg_color}" rx="20"/>
        <rect width="{width}" height="{height}" fill="url(#bgGradient)" rx="20" opacity="{bg_overlay_opacity}">
            <animate attributeName="opacity" values="{bg_overlay_opacity};0.5;{bg_overlay_opacity}" dur="4s" repeatCount="indefinite"/>
        </rect>
        
        <!-- Decorative circles with animation -->
        <circle cx="50" cy="50" r="80" fill="{decorative_circle_fill}">
            <animate attributeName="r" values="80;85;80" dur="6s" repeatCount="indefinite"/>
            <animate attributeName="opacity" values="0.3;0.5;0.3" dur="4s" repeatCount="indefinite"/>
        </circle>
        <circle cx="{width-50}" cy="{height-50}" r="100" fill="{decorative_circle_fill}">
            <animate attributeName="r" values="100;105;100" dur="8s" repeatCount="indefinite"/>
            <animate attributeName="opacity" values="0.3;0.5;0.3" dur="5s" repeatCount="indefinite"/>
        </circle>
        
        <!-- Theme-dependent Header Section -->
        <rect width="{width}" height="100" fill="{header_bg}" rx="20"/>
        <rect width="{width}" height="100" fill="url(#headerGrad)" rx="20" opacity="{header_overlay_opacity}">
            <animate attributeName="opacity" values="{header_overlay_opacity};0.6;{header_overlay_opacity}" dur="3s" repeatCount="indefinite"/>
        </rect>
        <use href="#rotatingCircle" x="350" y="50" opacity="0.2">
            <animate attributeName="opacity" values="0.2;0.35;0.2" dur="5s" repeatCount="indefinite"/>
        </use>
        
        <!-- Avatar circle with glow -->
        <a xlink:href="https://github.com/{safe_username}" target="_blank">
            <circle cx="60" cy="50" r="35" fill="{avatar_bg}" filter="url(#glow)"/>
            <circle cx="60" cy="50" r="32" fill="rgba(0,0,0,0.1)"/>
            {avatar_image_tag}
            <circle cx="60" cy="50" r="35" fill="none" stroke="{avatar_stroke}" stroke-width="2"/>
        </a>
        
        <!-- GitHub Logo next to avatar (no circle) -->
        <a xlink:href="https://github.com/{safe_username}" target="_blank">
            <g transform="translate(110, 50)">
                <g transform="translate(-12, -12) scale(0.4)">
                    <path d="{github_logo_path}" fill="{github_logo_fill}" opacity="1"/>
                </g>
                <title>View GitHub profile for {safe_username}</title>
            </g>
        </a>
        
        <!-- Username -->
        <a xlink:href="https://github.com/{safe_username}" target="_blank" style="text-decoration: none;">
            <text x="150" y="45" font-family="Inter, system-ui, sans-serif" font-size="28" font-weight="700" fill="{username_fill}" filter="url(#shadow)">
                {safe_username}
            </text>
        </a>
        
        <!-- Name -->
        <text x="150" y="70" font-family="Inter, system-ui, sans-serif" font-size="14" fill="{name_fill}">
            {safe_name}
        </text>
        
        <!-- Rating Badge -->
        <g transform="translate({width-80}, 30)">
            <circle r="30" fill="{rating_bg}" filter="url(#glow)"/>
            <circle r="26" fill="rgba(255,255,255,0.1)"/>
            <text x="0" y="8" font-family="Inter, system-ui, sans-serif" font-size="24" font-weight="800" fill="{rating_color}" text-anchor="middle" filter="url(#glow)">
                {rating}
            </text>
            <text x="0" y="22" font-family="Inter, system-ui, sans-serif" font-size="10" fill="{rating_label_fill}" text-anchor="middle">
                Rating
            </text>
        </g>
        
        <!-- Stats Grid -->
        <g transform="translate(30, 120)">
            <!-- Row 1 -->
            <!-- Stars -->
            <g transform="translate(0, 0)">
                <rect x="0" y="0" width="150" height="60" rx="12" fill="{card_bg}" opacity="0.95" filter="url(#shadow)"/>
                <rect x="0" y="0" width="150" height="4" rx="12" fill="url(#statGrad1)"/>
                <text x="15" y="25" font-family="Inter, system-ui, sans-serif" font-size="11" fill="{card_text_secondary}" font-weight="600">⭐ Stars</text>
                <text x="15" y="45" font-family="Inter, system-ui, sans-serif" font-size="22" font-weight="800" fill="url(#statGrad1)">{format_number(stats.total_stars)}</text>
            </g>
            
            <!-- Repositories -->
            <g transform="translate(170, 0)">
                <rect x="0" y="0" width="150" height="60" rx="12" fill="{card_bg}" opacity="0.95" filter="url(#shadow)"/>
                <rect x="0" y="0" width="150" height="4" rx="12" fill="url(#statGrad2)"/>
                <text x="15" y="25" font-family="Inter, system-ui, sans-serif" font-size="11" fill="{card_text_secondary}" font-weight="600">📦 Repos</text>
                <text x="15" y="45" font-family="Inter, system-ui, sans-serif" font-size="22" font-weight="800" fill="url(#statGrad2)">{stats.public_repos}</text>
            </g>
            
            <!-- Followers -->
            <g transform="translate(340, 0)">
                <rect x="0" y="0" width="150" height="60" rx="12" fill="{card_bg}" opacity="0.95" filter="url(#shadow)"/>
                <rect x="0" y="0" width="150" height="4" rx="12" fill="url(#statGrad3)"/>
                <text x="15" y="25" font-family="Inter, system-ui, sans-serif" font-size="11" fill="{card_text_secondary}" font-weight="600">👥 Followers</text>
                <text x="15" y="45" font-family="Inter, system-ui, sans-serif" font-size="22" font-weight="800" fill="url(#statGrad3)">{format_number(stats.followers)}</text>
            </g>
            
            <!-- Contributions -->
            <g transform="translate(510, 0)">
                <rect x="0" y="0" width="150" height="60" rx="12" fill="{card_bg}" opacity="0.95" filter="url(#shadow)"/>
                <rect x="0" y="0" width="150" height="4" rx="12" fill="url(#statGrad4)"/>
                <text x="15" y="25" font-family="Inter, system-ui, sans-serif" font-size="11" fill="{card_text_secondary}" font-weight="600">💻 Contributions</text>
                <text x="15" y="45" font-family="Inter, system-ui, sans-serif" font-size="22" font-weight="800" fill="url(#statGrad4)">{format_number(stats.total_contributions)}</text>
            </g>
            
            <!-- Row 2 -->
            <!-- Commits -->
            <g transform="translate(0, 80)">
                <rect x="0" y="0" width="150" height="60" rx="12" fill="{card_bg}" opacity="0.95" filter="url(#shadow)"/>
                <rect x="0" y="0" width="150" height="4" rx="12" fill="url(#statGrad5)"/>
                <text x="15" y="25" font-family="Inter, system-ui, sans-serif" font-size="11" fill="{card_text_secondary}" font-weight="600">📝 Commits (1Y)</text>
                <text x="15" y="45" font-family="Inter, system-ui, sans-serif" font-size="22" font-weight="800" fill="url(#statGrad5)">{format_number(stats.commits_last_year)}</text>
            </g>
            
            <!-- Pull Requests -->
            <g transform="translate(170, 80)">
                <rect x="0" y="0" width="150" height="60" rx="12" fill="{card_bg}" opacity="0.95" filter="url(#shadow)"/>
                <rect x="0" y="0" width="150" height="4" rx="12" fill="url(#statGrad6)"/>
                <text x="15" y="25" font-family="Inter, system-ui, sans-serif" font-size="11" fill="{card_text_secondary}" font-weight="600">🔀 Pull Requests</text>
                <text x="15" y="45" font-family="Inter, system-ui, sans-serif" font-size="22" font-weight="800" fill="url(#statGrad6)">{stats.pull_requests_last_year}</text>
            </g>
            
            <!-- Current Streak -->
            <g transform="translate(340, 80)">
                <rect x="0" y="0" width="150" height="60" rx="12" fill="{card_bg}" opacity="0.95" filter="url(#shadow)"/>
                <rect x="0" y="0" width="150" height="4" rx="12" fill="url(#statGrad7)"/>
                <text x="15" y="25" font-family="Inter, system-ui, sans-serif" font-size="11" fill="{card_text_secondary}" font-weight="600">🔥 Current Streak</text>
                <text x="15" y="45" font-family="Inter, system-ui, sans-serif" font-size="22" font-weight="800" fill="url(#statGrad7)">{stats.current_streak} days</text>
            </g>
            
            <!-- Top Language with icon -->
            <g transform="translate(510, 80)">
                <rect x="0" y="0" width="150" height="60" rx="12" fill="{card_bg}" opacity="0.95" filter="url(#shadow)"/>
                <rect x="0" y="0" width="150" height="4" rx="12" fill="url(#statGrad8)"/>
                <text x="15" y="25" font-family="Inter, system-ui, sans-serif" font-size="11" fill="{card_text_secondary}" font-weight="600">💬 Top Language</text>
                <g transform="translate(15, 35)">
                    <rect x="-10" y="-10" width="20" height="20" rx="4" fill="url(#statGrad8)" opacity="0.2"/>
                    <text x="0" y="5" font-family="Inter, system-ui, sans-serif" font-size="9" fill="url(#statGrad8)" text-anchor="middle" font-weight="700">
                        {lang_icon_text}
                    </text>
                </g>
                <text x="30" y="45" font-family="Inter, system-ui, sans-serif" font-size="15" font-weight="800" fill="url(#statGrad8)">{top_language}</text>
            </g>
        </g>
        
        <!-- Theme-dependent Footer -->
        <rect x="0" y="{height-50}" width="{width}" height="50" fill="{footer_bg}" rx="0 0 20 20"/>
        <rect x="0" y="{height-50}" width="{width}" height="50" fill="url(#headerGrad)" rx="0 0 20 20" opacity="{footer_overlay_opacity}"/>
        <a xlink:href="https://github.com/{safe_username}" target="_blank" style="text-decoration: none;">
            <text x="{width/2}" y="{height-20}" font-family="Inter, system-ui, sans-serif" font-size="14" font-weight="600" fill="{username_fill}" text-anchor="middle">
                View on GitHub →
            </text>
        </a>
    </svg>'''
    
    return svg_content

