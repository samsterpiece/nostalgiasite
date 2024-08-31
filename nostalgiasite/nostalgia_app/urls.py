from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'nostalgia_app'

urlpatterns = [
    path('', views.home, name='home'),
    path('submit-year/', views.submit_year, name='submit_year'),
    path('results/<int:grad_year>/', views.results, name='results'),
    path('api/changes/', views.api_changes, name='api_changes'),
    path('signup/', views.signup, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='nostalgia_app/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='nostalgia_app:home'), name='logout'),
    path('profile/', views.profile, name='profile'),
    path('about/', views.about, name='about'),
]