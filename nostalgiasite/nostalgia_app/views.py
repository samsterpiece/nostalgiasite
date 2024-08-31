import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.contrib.auth import login, authenticate
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Category, InformationItem, SignificantEvent, Book, UserSubmittedFact
from .serializers import CategorySerializer, InformationItemSerializer, SignificantEventSerializer, BookSerializer
from .forms import CustomUserCreationForm, FactSubmissionForm
from django.core.cache import cache
from django.views.decorators.http import require_http_methods
import requests

logger = logging.getLogger(__name__)

def home(request):
    current_year = timezone.now().year
    return render(request, 'nostalgia_app/home.html', {'current_year': current_year})

def submit_year(request):
    if request.method == 'POST':
        grad_year = request.POST.get('grad_year')
        if grad_year:
            return redirect('nostalgia_app:results', grad_year=grad_year)
        else:
            messages.error(request, "Please enter a valid graduation year.")
    return redirect('nostalgia_app:home')

def results(request, grad_year):
    try:
        current_year = timezone.now().year
        
        if not (1900 <= int(grad_year) <= current_year):
            messages.error(request, "Invalid graduation year. Please enter a year between 1900 and the current year.")
            return redirect('nostalgia_app:home')

        # Fetch data from APIs
        news_data = fetch_news_data(grad_year)
        book_data = fetch_book_data(grad_year)
        economic_data = fetch_economic_data(grad_year, current_year)

        # Fetch data from our database
        categories = Category.objects.all()
        significant_events = SignificantEvent.objects.filter(year=grad_year)
        information_items = InformationItem.objects.filter(year=grad_year)
        books = Book.objects.filter(year=grad_year)

        context = {
            'grad_year': grad_year,
            'current_year': current_year,
            'categories': categories,
            'significant_events': significant_events,
            'information_items': information_items,
            'books': books,
            'news_data': news_data,
            'book_data': book_data,
            'economic_data': economic_data,
        }

        return render(request, 'nostalgia_app/results.html', context)

    except Exception as e:
        logger.error(f"Unexpected error in results view: {str(e)}")
        messages.error(request, "An error occurred while processing your request. Please try again.")
        return redirect('nostalgia_app:home')

@login_required
@require_http_methods(["GET", "POST"])
def submit_fact(request):
    if request.method == 'POST':
        # Check rate limit
        user_id = request.user.id
        rate_limit_key = f'fact_submission_rate_limit_{user_id}'
        rate_limit = cache.get(rate_limit_key, 0)

        if rate_limit >= 5:  # Limit to 5 submissions per hour
            messages.error(request, "You've reached the maximum number of submissions per hour. Please try again later.")
            return redirect('nostalgia_app:home')

        form = FactSubmissionForm(request.POST)
        if form.is_valid():
            fact = form.save(commit=False)
            fact.user = request.user
            fact.save()
            form.save_m2m()  # Save many-to-many data
            messages.success(request, "Thank you for submitting a fact! It will be reviewed by our team.")
            
            # Increment rate limit
            cache.set(rate_limit_key, rate_limit + 1, 3600)  # 3600 seconds = 1 hour
            
            return redirect('nostalgia_app:home')
    else:
        form = FactSubmissionForm()
    return render(request, 'nostalgia_app/submit_fact.html', {'form': form})

@user_passes_test(lambda u: u.is_superuser)
def admin_dashboard(request):
    pending_facts = UserSubmittedFact.objects.filter(is_approved=False)
    return render(request, 'nostalgia_app/admin_dashboard.html', {'pending_facts': pending_facts})

@user_passes_test(lambda u: u.is_superuser)
def approve_fact(request, fact_id):
    fact = get_object_or_404(UserSubmittedFact, id=fact_id)
    fact.is_approved = True
    fact.save()
    messages.success(request, f"Fact '{fact.title}' has been approved.")
    return redirect('nostalgia_app:admin_dashboard')

@user_passes_test(lambda u: u.is_superuser)
def reject_fact(request, fact_id):
    fact = get_object_or_404(UserSubmittedFact, id=fact_id)
    fact.delete()
    messages.success(request, f"Fact '{fact.title}' has been rejected and deleted.")
    return redirect('nostalgia_app:admin_dashboard')

def fetch_news_data(year):
    # Implement API call to News API
    # Return formatted news data
    pass

def fetch_book_data(year):
    # Implement API call to Open Library API
    # Return formatted book data
    pass

def fetch_economic_data(start_year, end_year):
    # Implement API call to World Bank API
    # Return formatted economic data
    pass

def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Account created successfully!")
            return redirect('nostalgia_app:home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'nostalgia_app/signup.html', {'form': form})

@login_required
def profile(request):
    return render(request, 'nostalgia_app/profile.html')

def about(request):
    return render(request, 'nostalgia_app/about.html')

def error_404(request, exception):
    logger.warning(f"404 error: {request.path}")
    return render(request, 'nostalgia_app/404.html', status=404)

def error_500(request):
    logger.error(f"500 error occurred")
    return render(request, 'nostalgia_app/500.html', status=500)