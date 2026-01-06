"""
Views for the dashboard app.
"""
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_http_methods
from django.utils.html import escape
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


def generate_badge_svg(stats: GitHubStats, theme) -> str:
    """Generate modern, colorful SVG badge with comprehensive GitHub stats."""
    
    # Escape user input for security
    safe_username = escape(stats.username)
    safe_name = escape(stats.name[:40] if stats.name and len(stats.name) > 40 else (stats.name or safe_username))
    
    # Calculate rating with colors
    rating = "C+"
    rating_color = "#f59e0b"
    if stats.total_stars > 100:
        rating = "B+"
        rating_color = "#10b981"
    if stats.total_stars > 500:
        rating = "A"
        rating_color = "#3b82f6"
    if stats.total_stars > 1000:
        rating = "A+"
        rating_color = "#8b5cf6"
    
    # Get top language
    top_language = escape(stats.languages[0]['name'][:12]) if stats.languages else 'N/A'
    
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
    
    # Colorful gradients for stat cards
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
    
    svg_content = f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{width}" height="{height}">
        <defs>
            <!-- Animated background gradient -->
            <linearGradient id="bgGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style="stop-color:#667eea;stop-opacity:1">
                    <animate attributeName="stop-color" values="#667eea;#764ba2;#f093fb;#667eea" dur="15s" repeatCount="indefinite"/>
                </stop>
                <stop offset="50%" style="stop-color:#764ba2;stop-opacity:1">
                    <animate attributeName="stop-color" values="#764ba2;#f093fb;#667eea;#764ba2" dur="15s" repeatCount="indefinite"/>
                </stop>
                <stop offset="100%" style="stop-color:#f093fb;stop-opacity:1">
                    <animate attributeName="stop-color" values="#f093fb;#667eea;#764ba2;#f093fb" dur="15s" repeatCount="indefinite"/>
                </stop>
            </linearGradient>
            
            <!-- Header gradient -->
            <linearGradient id="headerGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style="stop-color:#667eea;stop-opacity:1" />
                <stop offset="100%" style="stop-color:#764ba2;stop-opacity:1" />
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
        </defs>
        
        <!-- Background with animated gradient -->
        <rect width="{width}" height="{height}" fill="url(#bgGradient)" rx="20"/>
        
        <!-- Decorative circles -->
        <circle cx="50" cy="50" r="80" fill="rgba(255,255,255,0.05)"/>
        <circle cx="{width-50}" cy="{height-50}" r="100" fill="rgba(255,255,255,0.05)"/>
        
        <!-- Header Section -->
        <rect width="{width}" height="100" fill="url(#headerGrad)" rx="20"/>
        <use href="#rotatingCircle" x="350" y="50" opacity="0.3"/>
        
        <!-- Avatar circle with glow -->
        <a xlink:href="https://github.com/{safe_username}" target="_blank">
            <circle cx="60" cy="50" r="35" fill="rgba(255,255,255,0.2)" filter="url(#glow)"/>
            <circle cx="60" cy="50" r="32" fill="white" opacity="0.1"/>
            <image xlink:href="{stats.avatar_url}" x="25" y="15" width="70" height="70" clip-path="circle(35px at 60px 50px)"/>
            <circle cx="60" cy="50" r="35" fill="none" stroke="rgba(255,255,255,0.4)" stroke-width="2"/>
        </a>
        
        <!-- Username -->
        <a xlink:href="https://github.com/{safe_username}" target="_blank" style="text-decoration: none;">
            <text x="110" y="45" font-family="Inter, system-ui, sans-serif" font-size="28" font-weight="700" fill="#ffffff" filter="url(#shadow)">
                {safe_username}
            </text>
        </a>
        
        <!-- Name -->
        <text x="110" y="70" font-family="Inter, system-ui, sans-serif" font-size="14" fill="rgba(255,255,255,0.9)">
            {safe_name}
        </text>
        
        <!-- Rating Badge -->
        <g transform="translate({width-80}, 30)">
            <circle r="30" fill="rgba(255,255,255,0.2)" filter="url(#glow)"/>
            <circle r="26" fill="rgba(255,255,255,0.1)"/>
            <text x="0" y="8" font-family="Inter, system-ui, sans-serif" font-size="24" font-weight="800" fill="{rating_color}" text-anchor="middle" filter="url(#glow)">
                {rating}
            </text>
            <text x="0" y="22" font-family="Inter, system-ui, sans-serif" font-size="10" fill="rgba(255,255,255,0.8)" text-anchor="middle">
                Rating
            </text>
        </g>
        
        <!-- Stats Grid -->
        <g transform="translate(30, 120)">
            <!-- Row 1 -->
            <!-- Stars -->
            <g transform="translate(0, 0)">
                <rect x="0" y="0" width="150" height="60" rx="12" fill="white" opacity="0.95" filter="url(#shadow)"/>
                <rect x="0" y="0" width="150" height="4" rx="12" fill="url(#statGrad1)"/>
                <text x="15" y="25" font-family="Inter, system-ui, sans-serif" font-size="11" fill="#6b7280" font-weight="600">⭐ Stars</text>
                <text x="15" y="45" font-family="Inter, system-ui, sans-serif" font-size="22" font-weight="800" fill="url(#statGrad1)">{format_number(stats.total_stars)}</text>
            </g>
            
            <!-- Repositories -->
            <g transform="translate(170, 0)">
                <rect x="0" y="0" width="150" height="60" rx="12" fill="white" opacity="0.95" filter="url(#shadow)"/>
                <rect x="0" y="0" width="150" height="4" rx="12" fill="url(#statGrad2)"/>
                <text x="15" y="25" font-family="Inter, system-ui, sans-serif" font-size="11" fill="#6b7280" font-weight="600">📦 Repos</text>
                <text x="15" y="45" font-family="Inter, system-ui, sans-serif" font-size="22" font-weight="800" fill="url(#statGrad2)">{stats.public_repos}</text>
            </g>
            
            <!-- Followers -->
            <g transform="translate(340, 0)">
                <rect x="0" y="0" width="150" height="60" rx="12" fill="white" opacity="0.95" filter="url(#shadow)"/>
                <rect x="0" y="0" width="150" height="4" rx="12" fill="url(#statGrad3)"/>
                <text x="15" y="25" font-family="Inter, system-ui, sans-serif" font-size="11" fill="#6b7280" font-weight="600">👥 Followers</text>
                <text x="15" y="45" font-family="Inter, system-ui, sans-serif" font-size="22" font-weight="800" fill="url(#statGrad3)">{format_number(stats.followers)}</text>
            </g>
            
            <!-- Contributions -->
            <g transform="translate(510, 0)">
                <rect x="0" y="0" width="150" height="60" rx="12" fill="white" opacity="0.95" filter="url(#shadow)"/>
                <rect x="0" y="0" width="150" height="4" rx="12" fill="url(#statGrad4)"/>
                <text x="15" y="25" font-family="Inter, system-ui, sans-serif" font-size="11" fill="#6b7280" font-weight="600">💻 Contributions</text>
                <text x="15" y="45" font-family="Inter, system-ui, sans-serif" font-size="22" font-weight="800" fill="url(#statGrad4)">{format_number(stats.total_contributions)}</text>
            </g>
            
            <!-- Row 2 -->
            <!-- Commits -->
            <g transform="translate(0, 80)">
                <rect x="0" y="0" width="150" height="60" rx="12" fill="white" opacity="0.95" filter="url(#shadow)"/>
                <rect x="0" y="0" width="150" height="4" rx="12" fill="url(#statGrad5)"/>
                <text x="15" y="25" font-family="Inter, system-ui, sans-serif" font-size="11" fill="#6b7280" font-weight="600">📝 Commits (1Y)</text>
                <text x="15" y="45" font-family="Inter, system-ui, sans-serif" font-size="22" font-weight="800" fill="url(#statGrad5)">{format_number(stats.commits_last_year)}</text>
            </g>
            
            <!-- Pull Requests -->
            <g transform="translate(170, 80)">
                <rect x="0" y="0" width="150" height="60" rx="12" fill="white" opacity="0.95" filter="url(#shadow)"/>
                <rect x="0" y="0" width="150" height="4" rx="12" fill="url(#statGrad6)"/>
                <text x="15" y="25" font-family="Inter, system-ui, sans-serif" font-size="11" fill="#6b7280" font-weight="600">🔀 Pull Requests</text>
                <text x="15" y="45" font-family="Inter, system-ui, sans-serif" font-size="22" font-weight="800" fill="url(#statGrad6)">{stats.pull_requests_last_year}</text>
            </g>
            
            <!-- Current Streak -->
            <g transform="translate(340, 80)">
                <rect x="0" y="0" width="150" height="60" rx="12" fill="white" opacity="0.95" filter="url(#shadow)"/>
                <rect x="0" y="0" width="150" height="4" rx="12" fill="url(#statGrad7)"/>
                <text x="15" y="25" font-family="Inter, system-ui, sans-serif" font-size="11" fill="#6b7280" font-weight="600">🔥 Current Streak</text>
                <text x="15" y="45" font-family="Inter, system-ui, sans-serif" font-size="22" font-weight="800" fill="url(#statGrad7)">{stats.current_streak} days</text>
            </g>
            
            <!-- Top Language -->
            <g transform="translate(510, 80)">
                <rect x="0" y="0" width="150" height="60" rx="12" fill="white" opacity="0.95" filter="url(#shadow)"/>
                <rect x="0" y="0" width="150" height="4" rx="12" fill="url(#statGrad8)"/>
                <text x="15" y="25" font-family="Inter, system-ui, sans-serif" font-size="11" fill="#6b7280" font-weight="600">💬 Top Language</text>
                <text x="15" y="45" font-family="Inter, system-ui, sans-serif" font-size="18" font-weight="800" fill="url(#statGrad8)">{top_language}</text>
            </g>
        </g>
        
        <!-- Footer -->
        <rect x="0" y="{height-50}" width="{width}" height="50" fill="url(#headerGrad)" rx="0 0 20 20"/>
        <a xlink:href="https://github.com/{safe_username}" target="_blank" style="text-decoration: none;">
            <text x="{width/2}" y="{height-20}" font-family="Inter, system-ui, sans-serif" font-size="14" font-weight="600" fill="#ffffff" text-anchor="middle">
                View on GitHub →
            </text>
        </a>
    </svg>'''
    
    return svg_content

