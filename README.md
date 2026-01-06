# GitHub Stats Generator

A beautiful Django-based GitHub statistics dashboard with multiple theme support and embeddable badges.

## Features

- 📊 Comprehensive GitHub statistics dashboard
- 🎨 Multiple beautiful themes (Neon Dark, Solar Dark, Light Clean, Minimal Dark)
- 📈 Interactive charts for contributions and activity
- 🏆 Contribution streaks tracking
- 💻 Language usage statistics
- 🖼️ Embeddable SVG badges for GitHub README
- ⚡ Caching for optimal performance
- 📱 Responsive design

The dashboard displays:
- User profile information
- Total contributions and activity
- Monthly and daily contribution charts
- Most used programming languages
- Current and longest contribution streaks
- GitHub stats (stars, commits, PRs, issues)

## Installation

### Prerequisites

- Python 3.8+
- Node.js and npm (for Tailwind CSS)
- Git

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd github-stat-generator
```

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install Python dependencies:
```bash
pip install -r requirements.txt
```

4. Install Tailwind CSS:
```bash
npm install
```

5. Build Tailwind CSS:
```bash
npm run build-css
```

For development with auto-rebuild:
```bash
npm run watch-css
```

6. Create a `.env` file (REQUIRED to avoid rate limits):
```bash
touch .env
```

Edit `.env` and add your GitHub token (REQUIRED):
```bash
# Generate a secret key
python manage.py shell -c "from django.core.management.utils import get_random_secret_key; print('SECRET_KEY=' + get_random_secret_key())"
```

Add to `.env`:
```
GITHUB_TOKEN=your_github_token_here
SECRET_KEY=your-secret-key-here
DEBUG=True
```

**Important: Get a GitHub token to avoid rate limits:**
1. Go to https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Give it a name (e.g., "GitHub Stats Generator")
4. Select expiration (or "No expiration" for development)
5. **No permissions needed** - public read-only access is enough
6. Click "Generate token" and copy it
7. Paste it in your `.env` file as `GITHUB_TOKEN=your_token_here`

**Without a token:** 60 requests/hour per IP  
**With a token:** 5,000 requests/hour

7. Run migrations:
```bash
python manage.py migrate
```

8. Collect static files:
```bash
python manage.py collectstatic --noinput
```

9. Start the development server:
```bash
python manage.py runserver
```

10. Open your browser and navigate to `http://127.0.0.1:8000`

## Usage

### Viewing Stats

1. Go to the home page
2. Enter a GitHub username
3. Click "View Stats" to see the dashboard

Or directly visit: `http://127.0.0.1:8000/u/<username>/`

### Changing Themes

- Use the theme dropdown in the navigation bar
- Themes are saved in a cookie and persist across sessions
- You can also use query parameters: `?theme=neon_dark`

Available themes:
- `neon_dark` - Neon blue accents on dark background
- `solar_dark` - Warm orange/yellow accents
- `light_clean` - Clean light theme
- `minimal_dark` - Minimal dark theme

### Embedding Badges

Add this to your GitHub README:

```markdown
![GitHub stats](https://your-domain.com/badge/USERNAME.svg?theme=neon_dark)
```

Replace:
- `your-domain.com` with your domain
- `USERNAME` with the GitHub username
- `theme` with your preferred theme (optional)

Example:
```markdown
![GitHub stats](https://your-domain.com/badge/octocat.svg?theme=neon_dark)
```

## Configuration

### Environment Variables

- `GITHUB_TOKEN` - GitHub API token (optional, increases rate limit)
- `SECRET_KEY` - Django secret key (required for production)
- `DEBUG` - Debug mode (set to `False` in production)

### Cache Settings

Stats are cached for 30 minutes by default. You can change this in `github_stats/settings.py`:

```python
GITHUB_CACHE_TIMEOUT = 1800  # seconds
```

## Screenshot

<img width="600" height="400" alt="11111" src="https://github.com/user-attachments/assets/5b961834-8071-460a-b6f5-8a56512a97ec" />
<img width="500" height="700" alt="Screenshot 2026-01-06 at 23-44-27 nahidn4p - GitHub Stats" src="https://github.com/user-attachments/assets/7e99c9c6-4da4-44d2-b244-2f63387ace62" />


## Project Structure

```
github-stat-generator/
├── dashboard/              # Main Django app
│   ├── services/          # GitHub API client
│   ├── templates/         # HTML templates
│   ├── themes.py          # Theme definitions
│   ├── views.py           # View handlers
│   └── urls.py            # URL routing
├── github_stats/          # Django project settings
├── static/                # Static files (CSS, JS)
├── manage.py              # Django management script
├── requirements.txt       # Python dependencies
├── package.json           # Node.js dependencies
└── tailwind.config.js     # Tailwind CSS configuration
```

## API Rate Limits

Without a GitHub token:
- 60 requests per hour per IP

With a GitHub token:
- 5,000 requests per hour

The app uses caching to minimize API calls. Stats are cached for 30 minutes.

## Development

### Running Tests

```bash
python manage.py test
```

### Building CSS

```bash
npm run build-css
```

### Watching CSS Changes

```bash
npm run watch-css
```

## Troubleshooting

### Rate Limit Errors

- Add a GitHub token to your `.env` file
- Wait for the cache to expire (30 minutes)
- Clear the cache: `python manage.py shell` → `from django.core.cache import cache; cache.clear()`

### User Not Found

- Verify the username is correct
- Check if the user exists on GitHub
- Ensure the user has public repositories

### CSS Not Loading

- Run `npm run build-css` to build Tailwind CSS
- Check that `static/css/output.css` exists
- Run `python manage.py collectstatic`

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgments

- Built with Django
- Styled with Tailwind CSS
- Charts powered by Chart.js
- Data from GitHub API

