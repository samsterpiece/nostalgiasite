import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.core.cache import cache
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.views.decorators.http import condition
from .models import Category, UserSubmittedFact, APIFact, SignificantEvent, Book
from .serializers import CategorySerializer, UserSubmittedFactSerializer, CombinedFactSerializer
from .forms import CustomUserCreationForm, FactSubmissionForm, FactReviewForm
from .tasks import update_significant_events, fetch_and_update_books
from .helpers import fetch_wikipedia_events, fetch_open_library_books, fetch_api_facts
import time


logger = logging.getLogger(__name__)

def home(request):
    """Render the home page."""
    try:
        current_year = timezone.now().year
        year_range = range(1900, current_year + 1)
        context = {
            'year_range': year_range,
            'current_year': current_year,
        }
        return render(request, 'nostalgia_app/home.html', context)
    except Exception as e:
        logger.error(f"Error in home view: {str(e)}")
        messages.error(request, "An error occurred while loading the home page.")
        return redirect('nostalgia_app:error')

def get_significant_events(year):
    """
    Get significant events for a given year.

    Args:
        year (int): The year to get events for.

    Returns:
        list: A list of SignificantEvent objects.
    """
    cache_key = f'significant_events_{year}'
    cached_events = cache.get(cache_key)

    if cached_events:
        return cached_events

    events = []
    try:
        db_events = SignificantEvent.objects.filter(year=year)
        events = list(db_events)

        if len(events) < 5:
            update_significant_events.delay(year)  # Trigger Celery task
            wiki_events = fetch_wikipedia_events(year, 5 - len(events))
            for event in wiki_events:
                new_event, created = SignificantEvent.objects.get_or_create(
                    year=year,
                    title=event['title'],
                    defaults={
                        'description': event['description'],
                        'source_url': event['source_url']
                    }
                )
                if created:
                    events.append(new_event)

    except Exception as e:
        logger.error(f"Error fetching significant events for {year}: {str(e)}")

    cache.set(cache_key, events, 86400)  # Cache for 24 hours
    return events

def get_recommended_reading(year, category_name='fiction'):
    """
    Get recommended reading for a given year and category.

    Args:
        year (int): The year to get books for.
        category_name (str): The category of books to get.

    Returns:
        list: A list of Book objects.
    """
    cache_key = f'recommended_reading_{year}_{category_name}'
    cached_books = cache.get(cache_key)

    if cached_books:
        return cached_books

    books = []
    try:
        db_books = Book.objects.filter(year=year, categories__name=category_name)
        books = list(db_books)

        if len(books) < 5:
            fetch_and_update_books.delay(year, category_name)

            open_library_books = fetch_open_library_books(year, category_name, 10 - len(books))
            for book_data in open_library_books:
                book, created = Book.objects.get_or_create(
                    title=book_data['title'],
                    author=book_data['author'],
                    year=year,
                    defaults={
                        'description': book_data['description'],
                        'cover_url': book_data['cover_url'],
                        'relevance': f"Published in {year}, related to {category_name}",
                    }
                )
                if created:
                    # Ensure category is fetched or created safely.
                    category, _ = Category.objects.get_or_create(
                        name=category_name,
                        defaults={'slug': category_name.lower().replace(' ', '_')}
                    )
                    book.categories.add(category)

                if book not in books:
                    books.append(book)

        books = books[:10]  # Limit to 10 books

    except Exception as e:
        logger.error(f"Error fetching recommended reading for {year} and category {category_name}: {str(e)}")

    cache.set(cache_key, books, 86400)  # Cache for 24 hours
    return books

@api_view(['GET'])
def results_api(request, grad_year):
    """API endpoint for getting results."""
    try:
        selected_category = request.GET.get('category', 'all')
        page_number = request.GET.get('page', 1)
        cache_key = f'results_{grad_year}_{selected_category}_{page_number}'

        timestamp = int(time.time())
        cache_key = f'{cache_key}_{timestamp}'

        cached_data = cache.get(cache_key)

        if cached_data:
            response = Response(cached_data)
            response['Cache-Control'] = 'no-cache, must-revalidate'
            response['Pragma'] = 'no-cache'
            return response

        categories = Category.objects.all()

        user_facts = UserSubmittedFact.objects.filter(status='approved', year=grad_year)
        api_facts = APIFact.objects.filter(year=grad_year)
        all_facts = list(user_facts) + list(api_facts)

        if selected_category != 'all':
            category = get_object_or_404(Category, slug=selected_category)
            all_facts = [fact for fact in all_facts if category in fact.categories.all()]

        paginator = Paginator(all_facts, 10)  # Show 10 facts per page
        page_obj = paginator.get_page(page_number)

        serialized_facts = CombinedFactSerializer(page_obj, many=True).data

        significant_events = get_significant_events(grad_year)
        recommended_reading = get_recommended_reading(year=grad_year, category_name=selected_category if selected_category != 'all' else 'fiction')

        context = {
            'categories': CategorySerializer(categories, many=True).data,
            'facts': serialized_facts,
            'significant_events': [
                {
                    'title': event.title,
                    'description': event.description,
                    'impact': event.impact,
                    'source_url': event.source_url,
                    'year': event.year
                } for event in significant_events],
            'recommended_reading': [
                {
                    'title': book.title,
                    'description': book.description,
                    'author': book.author,
                    'source_url': book.source_url,
                    'cover_url': book.cover_url,
                    'year': book.year,
                    'categories': [cat.name for cat in book.categories.all()],
                    'relevance': book.relevance
                } for book in recommended_reading
            ],
            'has_next': page_obj.has_next(),
            'total_pages': paginator.num_pages,
        }

        cache.set(cache_key, context, 3600)  # Cache for 1 hour

        response = Response(context)
        response['Cache-Control'] = 'no-cache, must-revalidate'
        response['Pragma'] = 'no-cache'
        return response

    except Exception as e:
        logger.error(f"Error in results_api for year {grad_year}: {str(e)}")
        return Response({'error': 'An error occurred while fetching results'}, status=500)


@login_required
def submit_fact(request):
    if request.method == 'POST':
        user_id = request.user.id
        rate_limit_key = f'fact_submission_rate_limit_{user_id}'
        rate_limit = cache.get(rate_limit_key, 0)

        if rate_limit >= 5:
            messages.error(request, "You've reached the maximum number of submissions per hour. Please try again later.")
            return redirect('nostalgia_app:home')

        form = FactSubmissionForm(request.POST)
        if form.is_valid():
            fact = form.save(commit=False)
            fact.user = request.user
            fact.save()
            form.save_m2m()
            messages.success(request, "Thank you for submitting a fact! It will be reviewed by our team.")
            cache.set(rate_limit_key, rate_limit + 1, 3600)
            return redirect('nostalgia_app:home')
        else:
            messages.error(request, "There was an error submitting your fact. Please correct the errors below.")
    else:
        form = FactSubmissionForm()

    categories = Category.objects.all()
    current_year = timezone.now().year
    year_range = range(1900, current_year + 1)
    context = {
        'form': form,
        'categories': categories,
        'year_range': year_range,
    }

    return render(request, 'nostalgiasite/nostalgia_app/templates/nostalgia_app/submit_fact.html', context)

@login_required
def submit_fact(request):
    if request.method == 'POST':
        user_id = request.user.id
        rate_limit_key = f'fact_submission_rate_limit_{user_id}'
        rate_limit = cache.get(rate_limit_key, 0)

        if rate_limit >= 5:
            messages.error(request,
                           "You've reached the maximum number of submissions per hour. Please try again later.")
            return redirect('nostalgia_app:home')

        form = FactSubmissionForm(request.POST)
        if form.is_valid():
            fact = form.save(commit=False)
            fact.user = request.user
            fact.save()
            form.save_m2m()
            messages.success(request, "Thank you for submitting a fact! It will be reviewed by our team.")

            cache.set(rate_limit_key, rate_limit + 1, 3600)

            return redirect('nostalgia_app:home')
    else:
        form = FactSubmissionForm()

    categories = Category.objects.all()
    return render(request, 'nostalgia_app/submit_fact.html', {'form': form, 'categories': categories})

@user_passes_test(lambda u: u.is_superuser)
def admin_dashboard(request):
    """Render the admin dashboard."""
    try:
        under_review = UserSubmittedFact.objects.filter(status='under_review')
        approved = UserSubmittedFact.objects.filter(status='approved')
        denied = UserSubmittedFact.objects.filter(status='denied')
        undetermined = UserSubmittedFact.objects.filter(status='undetermined')

        context = {
            'under_review': UserSubmittedFactSerializer(under_review, many=True).data,
            'approved': UserSubmittedFactSerializer(approved, many=True).data,
            'denied': UserSubmittedFactSerializer(denied, many=True).data,
            'undetermined': UserSubmittedFactSerializer(undetermined, many=True).data,
        }
        return render(request, 'nostalgia_app/admin_dashboard.html', context)
    except Exception as e:
        logger.error(f"Error in admin_dashboard view: {str(e)}")
        messages.error(request, "An error occurred while loading the dashboard.")
        return redirect('nostalgia_app:home')

@user_passes_test(lambda u: u.is_superuser)
def review_fact(request, fact_id):
    """Handle fact review."""
    try:
        fact = get_object_or_404(UserSubmittedFact, id=fact_id)
        if request.method == 'POST':
            form = FactReviewForm(request.POST, instance=fact)
            if form.is_valid():
                fact = form.save(commit=False)
                fact.reviewed_by = request.user
                fact.reviewed_at = timezone.now()
                fact.save()
                messages.success(request, f"Fact '{fact.title}' has been updated.")
                return redirect('nostalgia_app:admin_dashboard')
        else:
            form = FactReviewForm(instance=fact)

        return render(request, 'nostalgia_app/review_fact.html',
                      {'form': form, 'fact': UserSubmittedFactSerializer(fact).data})
    except Exception as e:
        logger.error(f"Error in review_fact view for fact_id {fact_id}: {str(e)}")
        messages.error(request, "An error occurred while reviewing the fact.")
        return redirect('nostalgia_app:admin_dashboard')

def signup(request):
    """Handle user signup."""
    try:
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
    except Exception as e:
        logger.error(f"Error in signup view: {str(e)}")
        messages.error(request, "An error occurred during signup.")
        return redirect('nostalgia_app:home')

@user_passes_test(lambda u: u.is_superuser)
def approve_fact(request, fact_id):
    """Approve a submitted fact."""
    try:
        fact = get_object_or_404(UserSubmittedFact, id=fact_id)
        fact.status = 'approved'
        fact.save()
        messages.success(request, f"Fact '{fact.title}' has been approved.")
        return redirect('nostalgia_app:admin_dashboard')
    except Exception as e:
        logger.error(f"Error in approve_fact view for fact_id {fact_id}: {str(e)}")
        messages.error(request, "An error occurred while approving the fact.")
        return redirect('nostalgia_app:admin_dashboard')

@user_passes_test(lambda u: u.is_superuser)
def reject_fact(request, fact_id):
    """Reject a submitted fact."""
    try:
        fact = get_object_or_404(UserSubmittedFact, id=fact_id)
        fact.status = 'denied'
        fact.save()
        messages.success(request, f"Fact '{fact.title}' has been rejected.")
        return redirect('nostalgia_app:admin_dashboard')
    except Exception as e:
        logger.error(f"Error in reject_fact view for fact_id {fact_id}: {str(e)}")
        messages.error(request, "An error occurred while rejecting the fact.")
        return redirect('nostalgia_app:admin_dashboard')

@login_required
def profile(request):
    """Render the user profile page."""
    try:
        user_facts = UserSubmittedFact.objects.filter(user=request.user)
        context = {
            'user': request.user,
            'user_facts': UserSubmittedFactSerializer(user_facts, many=True).data
        }
        return render(request, 'nostalgia_app/profile.html', context)
    except Exception as e:
        logger.error(f"Error in profile view for user {request.user.id}: {str(e)}")
        messages.error(request, "An error occurred while loading your profile.")
        return redirect('nostalgia_app:home')

def about(request):
    """Render the about page."""
    try:
        return render(request, 'nostalgia_app/about.html')
    except Exception as e:
        logger.error(f"Error in about view: {str(e)}")
        messages.error(request, "An error occurred while loading the about page.")
        return redirect('nostalgia_app:home')

def error_404(request, exception):
    """Handle 404 errors."""
    logger.warning(f"404 error: {request.path}")
    return render(request, 'nostalgia_app/404.html', status=404)

def error_500(request):
    """Handle 500 errors."""
    logger.error(f"500 error occurred")
    return render(request, 'nostalgia_app/500.html', status=500)

def error(request):
    """Handle general errors."""
    return render(request, 'nostalgia_app/error.html')

def submit_year(request):
    """Handle year submission."""
    if request.method == 'POST':
        grad_year = request.POST.get('grad_year')
        if grad_year:
            request.session['last_searched_year'] = grad_year
            return JsonResponse({'success': True, 'grad_year': grad_year})
        else:
            return JsonResponse({'success': False, 'error': 'Invalid graduation year'})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

def results_view(request, grad_year):
    """Render the results page."""
    try:
        categories = Category.objects.all()
        searched_years = request.session.get('searched_years', [])

        if not searched_years or int(grad_year) != int(searched_years[0]):
            searched_years.insert(0, int(grad_year))
            searched_years = searched_years[:5]  # Keep only the 5 most recent searches
            request.session['searched_years'] = searched_years

        context = {
            'grad_year': grad_year,
            'categories': categories,
            'searched_years': searched_years[1:],  # Exclude the current year from previous searches
        }
        return render(request, 'nostalgia_app/results.html', context)
    except Exception as e:
        logger.error(f"Error in results_view: {str(e)}")
        messages.error(request, "An error occurred while loading the results page.")
        return redirect('nostalgia_app:error')

def last_modified(request, grad_year):
    """Get the last modified time for a given year."""
    latest_times = []

    user_fact = UserSubmittedFact.objects.filter(year=grad_year).order_by('-submitted_at').first()
    if user_fact:
        latest_times.append(max(user_fact.submitted_at, user_fact.reviewed_at or user_fact.submitted_at))

    api_fact = APIFact.objects.filter(year=grad_year).order_by('-created_at').first()
    if api_fact:
        latest_times.append(api_fact.created_at)

    event = SignificantEvent.objects.filter(year=grad_year).order_by('-id').first()
    if event:
        latest_times.append(timezone.now())

    book = Book.objects.filter(year=grad_year).order_by('-id').first()
    if book:
        latest_times.append(timezone.now())

    return max(latest_times) if latest_times else None

def is_admin(user):
    """Check if a user is an admin."""
    return user.is_authenticated and user.is_superuser