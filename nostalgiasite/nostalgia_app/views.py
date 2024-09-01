import logging
from http.client import HTTPResponse

from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Category, UserSubmittedFact, APIFact
from .serializers import CategorySerializer, UserSubmittedFactSerializer, APIFactSerializer, CombinedFactSerializer
from .forms import CustomUserCreationForm, FactSubmissionForm, FactReviewForm
from django.core.cache import cache
import wikipedia
from django.http import JsonResponse

def index(request):
    my_dictionary = {"a": 1, "b": 2}
    return JsonResponse(my_dictionary)

def index2(request):
    my_array = [("a", 1), ("b", 2)]
    return JsonResponse(my_array, safe=False)


logger = logging.getLogger(__name__)


def is_admin(user):
    return user.is_authenticated and user.is_superuser


def home(request):
    current_year = timezone.now().year
    year_range = range(1900, current_year + 1)
    context = {
        'year_range': year_range,
        'current_year': current_year,
    }
    return render(request, 'nostalgia_app/home.html', context)


def submit_year(request):
    if request.method == 'POST':
        grad_year = request.POST.get('grad_year')
        if grad_year:
            request.session['last_searched_year'] = grad_year
            return JsonResponse({'success': True, 'grad_year': grad_year})
        else:
            return JsonResponse({'success': False, 'error': 'Invalid graduation year'})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


def results_view(request, grad_year):
    try:
        categories = Category.objects.all()
        searched_years = request.session.get('searched_years', [])

        # Only add the year to searched_years if it's not already the most recent search
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
        return HTTPResponse(f"An error occurred: {str(e)}", status=500)


@api_view(['GET'])
def results_api(request, grad_year):
    categories = Category.objects.all()
    selected_category = request.GET.get('category')

    user_facts = UserSubmittedFact.objects.filter(status='approved', year=grad_year)
    api_facts = fetch_api_facts(grad_year)

    user_facts_serializer = UserSubmittedFactSerializer(user_facts, many=True)
    api_facts_serializer = APIFactSerializer(api_facts, many=True)

    all_facts = []
    for fact in user_facts_serializer.data:
        fact['fact_type'] = 'user_submitted'
        all_facts.append(fact)
    for fact in api_facts_serializer.data:
        fact['fact_type'] = 'api'
        all_facts.append(fact)

    if selected_category:
        all_facts = [fact for fact in all_facts if selected_category in [cat['name'] for cat in fact['categories']]]

    context = {
        'categories': CategorySerializer(categories, many=True).data,
        'facts': CombinedFactSerializer(all_facts, many=True).data,
        'significant_events': get_significant_events(grad_year),
        'recommended_reading': get_recommended_reading(grad_year),
    }

    return Response(context)


def fetch_api_facts(grad_year):
    for category in Category.objects.all():
        try:
            search_query = f"{grad_year} {category.name}"
            search_results = wikipedia.search(search_query, results=5)

            for result in search_results:
                try:
                    page = wikipedia.page(result, auto_suggest=False)

                    if str(grad_year) in page.title or str(grad_year) in page.content[:500]:
                        summary = page.summary.split('. ')[0].strip()

                        if str(grad_year) not in summary:
                            summary = f"In {grad_year}, " + summary

                        try:
                            fact, created = APIFact.objects.get_or_create(
                                year=grad_year,
                                title=page.title,
                                defaults={
                                    'description': summary,
                                    'source_url': page.url
                                }
                            )
                            fact.categories.add(category)
                            if not created:
                                fact.description = summary
                                fact.save()
                        except IntegrityError:
                            pass

                        break
                except (wikipedia.exceptions.DisambiguationError, wikipedia.exceptions.PageError):
                    continue
        except Exception as e:
            logger.error(f"Error fetching facts for {grad_year} in {category.name}: {str(e)}")

    return APIFact.objects.filter(year=grad_year)


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


@user_passes_test(is_admin)
def admin_dashboard(request):
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


@user_passes_test(is_admin)
def review_fact(request, fact_id):
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
                return redirect('nostalgia_app:admin_dashboard')
            except Exception as e:
                logger.error(f"Error updating fact: {str(e)}")
                messages.error(request, "An error occurred while updating the fact.")
    else:
        form = FactReviewForm(instance=fact)

    return render(request, 'nostalgia_app/review_fact.html',
                  {'form': form, 'fact': UserSubmittedFactSerializer(fact).data})


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

def get_significant_events(year):
    # Placeholder function
    return []


def get_recommended_reading(year):
    # Placeholder function
    return []

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