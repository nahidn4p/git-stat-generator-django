"""
URL configuration for dashboard app.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('u/<str:username>/', views.stats_view, name='stats'),
    path('badge/<str:username>.svg', views.badge_view, name='badge'),
    path('set-theme/', views.set_theme_view, name='set_theme'),
]

