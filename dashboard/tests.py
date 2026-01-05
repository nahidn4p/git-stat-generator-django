"""
Tests for the dashboard app.
"""
from django.test import TestCase, Client
from unittest.mock import patch, MagicMock
from .services.github_client import GitHubClient, GitHubStats
from .themes import get_theme, get_all_themes, DEFAULT_THEME
from datetime import datetime, timedelta
import json


class ThemeTests(TestCase):
    """Tests for theme system."""
    
    def test_get_theme_default(self):
        """Test getting default theme."""
        theme = get_theme('neon_dark')
        self.assertEqual(theme.id, 'neon_dark')
        self.assertEqual(theme.name, 'Neon Dark')
    
    def test_get_theme_invalid(self):
        """Test getting invalid theme returns default."""
        theme = get_theme('invalid_theme')
        self.assertEqual(theme.id, DEFAULT_THEME)
    
    def test_get_all_themes(self):
        """Test getting all themes."""
        themes = get_all_themes()
        self.assertGreater(len(themes), 0)
        self.assertTrue(all(isinstance(t, type(get_theme('neon_dark'))) for t in themes))


class GitHubClientTests(TestCase):
    """Tests for GitHub client."""
    
    @patch('dashboard.services.github_client.requests.get')
    def test_get_user_stats_success(self, mock_get):
        """Test successful user stats retrieval."""
        # Mock user data
        mock_user_response = MagicMock()
        mock_user_response.json.return_value = {
            'login': 'testuser',
            'name': 'Test User',
            'avatar_url': 'https://example.com/avatar.jpg',
            'bio': 'Test bio',
            'public_repos': 10,
            'followers': 5,
            'following': 3,
            'created_at': '2020-01-01T00:00:00Z',
        }
        mock_user_response.raise_for_status = MagicMock()
        
        # Mock repos response
        mock_repos_response = MagicMock()
        mock_repos_response.json.return_value = [
            {
                'name': 'repo1',
                'stargazers_count': 10,
                'language': 'Python',
                'size': 1000,
                'owner': {'login': 'testuser'},
            }
        ]
        mock_repos_response.raise_for_status = MagicMock()
        
        # Mock events response
        mock_events_response = MagicMock()
        mock_events_response.json.return_value = []
        mock_events_response.raise_for_status = MagicMock()
        
        mock_get.side_effect = [
            mock_user_response,
            mock_repos_response,
            mock_events_response,
        ]
        
        client = GitHubClient()
        stats = client.get_user_stats('testuser')
        
        self.assertEqual(stats.username, 'testuser')
        self.assertEqual(stats.name, 'Test User')
        self.assertEqual(stats.public_repos, 10)
    
    @patch('dashboard.services.github_client.requests.get')
    def test_get_user_stats_not_found(self, mock_get):
        """Test handling of user not found."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception()
        mock_response.status_code = 404
        
        import requests
        error = requests.HTTPError()
        error.response = mock_response
        mock_get.side_effect = error
        
        client = GitHubClient()
        with self.assertRaises(ValueError):
            client.get_user_stats('nonexistent')


class ViewTests(TestCase):
    """Tests for views."""
    
    def setUp(self):
        self.client = Client()
    
    def test_home_view(self):
        """Test home page loads."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'GitHub Stats Generator')
    
    @patch('dashboard.views.GitHubClient')
    def test_stats_view_success(self, mock_client_class):
        """Test stats view with successful data fetch."""
        # Mock stats
        mock_stats = MagicMock()
        mock_stats.username = 'testuser'
        mock_stats.name = 'Test User'
        mock_stats.daily_contributions = []
        mock_stats.monthly_contributions = []
        
        # Mock client
        mock_client = MagicMock()
        mock_client.get_user_stats.return_value = mock_stats
        mock_client_class.return_value = mock_client
        
        response = self.client.get('/u/testuser/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'testuser')
    
    @patch('dashboard.views.GitHubClient')
    def test_stats_view_not_found(self, mock_client_class):
        """Test stats view with user not found."""
        mock_client = MagicMock()
        mock_client.get_user_stats.side_effect = ValueError("User 'testuser' not found")
        mock_client_class.return_value = mock_client
        
        response = self.client.get('/u/testuser/')
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, 'Error')
    
    def test_set_theme_view(self):
        """Test theme setting view."""
        response = self.client.post('/set-theme/', {
            'theme': 'solar_dark',
            'redirect': '/',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.cookies['theme'].value, 'solar_dark')
    
    @patch('dashboard.views.GitHubClient')
    def test_badge_view(self, mock_client_class):
        """Test badge SVG generation."""
        mock_stats = MagicMock()
        mock_stats.username = 'testuser'
        mock_stats.name = 'Test User'
        mock_stats.total_stars = 100
        mock_stats.public_repos = 10
        mock_stats.current_streak = 5
        mock_stats.total_contributions = 500
        mock_stats.created_at = '2020-01-01T00:00:00Z'
        
        mock_client = MagicMock()
        mock_client.get_user_stats.return_value = mock_stats
        mock_client_class.return_value = mock_client
        
        response = self.client.get('/badge/testuser.svg')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/svg+xml')
        self.assertIn('testuser', response.content.decode())

