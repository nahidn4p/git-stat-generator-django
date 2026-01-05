# Setting Up GitHub Token

## Why You Need a GitHub Token

Without a GitHub token, you're limited to **60 API requests per hour**. This will cause "Rate Limit Exceeded" errors very quickly.

With a token, you get **5,000 requests per hour** - enough for normal usage.

## Quick Setup Guide

### Step 1: Create GitHub Personal Access Token

1. Go to: https://github.com/settings/tokens
2. Click **"Generate new token"** → **"Generate new token (classic)"**
3. Fill in:
   - **Note**: `GitHub Stats Generator` (or any name you prefer)
   - **Expiration**: Choose your preference (or "No expiration" for development)
   - **Select scopes**: **NONE needed** - public read-only access is sufficient
4. Click **"Generate token"**
5. **Copy the token immediately** (you won't see it again!)

### Step 2: Add Token to Your Project

1. Create a `.env` file in the project root (if it doesn't exist):
   ```bash
   touch .env
   ```

2. Add your token to `.env`:
   ```bash
   GITHUB_TOKEN=ghp_your_token_here
   SECRET_KEY=your-secret-key-here
   DEBUG=True
   ```

3. Generate a Django secret key:
   ```bash
   python manage.py shell -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```
   Copy the output and add it as `SECRET_KEY` in your `.env` file.

4. Restart your Django server:
   ```bash
   # Stop the server (Ctrl+C) and restart
   python manage.py runserver
   ```

### Step 3: Verify It Works

Try accessing a GitHub user's stats. If you still get rate limit errors:
- Make sure the `.env` file is in the project root (same directory as `manage.py`)
- Check that `GITHUB_TOKEN` is spelled correctly (no spaces around `=`)
- Restart your Django server after adding the token
- Verify the token is valid at: https://api.github.com/user (requires authentication)

## Troubleshooting

### "Rate limit exceeded" even with token
- Check your token is valid: https://api.github.com/user
- Verify `.env` file is in the correct location
- Make sure you restarted the server after adding the token
- Check Django logs for any errors loading the token

### Token not working
- Make sure there are no quotes around the token value
- No spaces before/after the `=` sign
- Token should start with `ghp_` for classic tokens
- Check `.env` file permissions (should be readable)

### Still having issues?
- Check the error page for detailed instructions
- Verify your token has the correct format
- Try generating a new token if the current one doesn't work

