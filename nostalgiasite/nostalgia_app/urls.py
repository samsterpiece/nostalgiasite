from django.urls import path
from . import views

app_name = 'nostalgia_app'

urlpatterns = [
    path('', views.home, name='home'),
    path('', views.about, name='about'),
    path('', views.api_changes, name='api_changes'),
    path('', views.results, name='results'),
    path('results/<int:grad_year>/', views.results, name='results'),
    path('api/changes/', views.api_changes, name='api_changes'),
]