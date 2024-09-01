from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.contrib import admin
from django.urls import path, include
from . import views

app_name = 'nostalgia_app'

urlpatterns = [
    path('', views.home, name='home'),
    path('submit-year/', views.submit_year, name='submit_year'),
    path('results/<int:grad_year>/', views.results_view, name='results'),
    path('api/results/<int:grad_year>/', views.results_api, name='results_api'),
    path('submit-fact/', views.submit_fact, name='submit_fact'),
    path('signup/', views.signup, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='nostalgia_app/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='nostalgia_app:home'), name='logout'),
    path('profile/', views.profile, name='profile'),
    path('about/', views.about, name='about'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('approve-fact/<int:fact_id>/', views.approve_fact, name='approve_fact'),
    path('reject-fact/<int:fact_id>/', views.reject_fact, name='reject_fact'),
    path('review-fact/<int:fact_id>/', views.review_fact, name='review_fact'),
]