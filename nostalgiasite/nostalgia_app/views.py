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
from .forms import FactReviewForm

logger = logging.getLogger(__name__)

def is_admin(user):
    return user.is_authenticated and user.is_superuser

def home(request):
    current_year = timezone.now().year
    years = list(range(1930, current_year + 1))  # Generate a list of years from 1930 to the current year
    return render(request, 'nostalgia_app/home.html', {'current_year': current_year, 'years': years})

def submit_year(request):
    if request.method == 'POST':
        grad_year = request.POST.get('grad_year')
        if grad_year:
            return redirect('nostalgia_app:results', grad_year=grad_year)
        else:
            messages.error(request, "Please enter a valid graduation year.")
    return redirect('nostalgia_app:home')

def results(request, grad_year):
    categories = Category.objects.all()
    selected_category = request.GET.get('category')

    # Fetch approved user-submitted facts
    user_facts = UserSubmittedFact.objects.filter(
        status='approved',
        year=grad_year
    )

    # Fetch API results (placeholder for now)
    api_facts = fetch_api_facts(grad_year)

    # Combine and process facts
    all_facts = process_facts(user_facts, api_facts)

    # Filter by category if selected
    if selected_category:
        all_facts = [fact for fact in all_facts if selected_category in fact['categories']]

    # Get or initialize the list of searched years from the session
    searched_years = request.session.get('searched_years', [])

    # Add the current year to the list if it's not already there
    if grad_year not in searched_years:
        searched_years.insert(0, grad_year)  # Add to the beginning of the list
        searched_years = searched_years[:5]  # Keep only the 5 most recent searches
        request.session['searched_years'] = searched_years

    context = {
        'grad_year': grad_year,
        'categories': categories,
        'selected_category': selected_category,
        'facts': all_facts,
        'significant_events': get_significant_events(grad_year),
        'recommended_reading': get_recommended_reading(grad_year),
        'searched_years': searched_years,
    }
    return render(request, 'nostalgia_app/results.html', context)

def fetch_api_facts(grad_year):
    # Placeholder for API calls
    # You would implement actual API calls here
    return []

def process_facts(user_facts, api_facts):
    processed_facts = []
    for fact in user_facts:
        processed_facts.append({
            'year': fact.year,
            'title': summarize_fact(fact.description),
            'description': fact.description,
            'categories': [cat.name for cat in fact.categories.all()],
            'source_url': fact.source_url
        })
    # Process API facts similarly
    # ...
    return processed_facts

def summarize_fact(description):
    # Simple summarization - take the first sentence
    return description.split('.')[0]

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
            form.save_m2m()  # Save many-to-many data (categories)
            messages.success(request, "Thank you for submitting a fact! It will be reviewed by our team.")

            # Increment rate limit
            cache.set(rate_limit_key, rate_limit + 1, 3600)  # 3600 seconds = 1 hour

            return redirect('nostalgia_app:home')
    else:
        form = FactSubmissionForm()

    categories = Category.objects.all()
    return render(request, 'nostalgia_app/submit_fact.html', {'form': form, 'categories': categories})

@user_passes_test(is_admin)
def admin_dashboard(request):
    """
    Renders the admin dashboard with tabs for different fact statuses.
    """
    try:
        under_review = UserSubmittedFact.objects.filter(status='under_review')
        approved = UserSubmittedFact.objects.filter(status='approved')
        denied = UserSubmittedFact.objects.filter(status='denied')
        undetermined = UserSubmittedFact.objects.filter(status='undetermined')

        context = {
            'under_review': under_review,
            'approved': approved,
            'denied': denied,
            'undetermined': undetermined,
        }
        return render(request, 'nostalgia_app/admin_dashboard.html', context)
    except Exception as e:
        logger.error(f"Error in admin_dashboard view: {str(e)}")
        messages.error(request, "An error occurred while loading the dashboard.")
        return redirect('nostalgia_app:home')

@user_passes_test(is_admin)
def review_fact(request, fact_id):
    """
    Allows admins to review and update the status of a submitted fact.
    """
    fact = get_object_or_404(UserSubmittedFact, id=fact_id)
    if request.method == 'POST':
        form = FactReviewForm(request.POST, instance=fact)
        if form.is_valid():
            try:
                fact = form.save(commit=False)
                fact.reviewed_by = request.user
                fact.reviewed_at = timezone.now()
                fact.save()
                messages.success(request, f"Fact '{fact.title}' has been updated.")
                # Here you would add logic to send notification to the user
                return redirect('nostalgia_app:admin_dashboard')
            except Exception as e:
                logger.error(f"Error updating fact: {str(e)}")
                messages.error(request, "An error occurred while updating the fact.")
    else:
        form = FactReviewForm(instance=fact)

    return render(request, 'nostalgia_app/review_fact.html', {'form': form, 'fact': fact})

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

def get_significant_events(year):
    # Placeholder function to get significant events for a specific year
    # Replace this with actual logic to fetch events from your database or API
    return []

def get_recommended_reading(year):
    # Placeholder function to get recommended reading for a specific year
    # Replace this with actual logic to fetch recommendations from your database or API
    return []

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