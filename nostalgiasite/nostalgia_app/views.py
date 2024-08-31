import logging
from django.shortcuts import render, redirect
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.views.decorators.http import require_GET
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Category, InformationItem, SignificantEvent, Book
from .serializers import (
    CategorySerializer,
    InformationItemSerializer,
    SignificantEventSerializer,
    BookSerializer
)

logger = logging.getLogger(__name__)

@require_GET
def home(request):
    """
    Render the home page of the Nostalgia Site.

    This view displays the initial page where users can input their graduation year.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Rendered home.html template.
    """
    try:
        return render(request, 'home.html')
    except Exception as e:
        logger.error(f"Error rendering home page: {str(e)}")
        return render(request, '500.html', status=500)

def results(request, grad_year):
    """
    Display results based on the user's graduation year and selected category.

    This view fetches and organizes information about changes, developments,
    and events that have occurred since the user's graduation year. It also
    provides book recommendations based on the selected category.

    Args:
        request (HttpRequest): The HTTP request object.
        grad_year (int): The user's graduation year.

    Returns:
        HttpResponse: Rendered results.html template with context data.
    """
    try:
        current_year = timezone.now().year
        
        if not (1900 <= grad_year <= current_year):
            messages.error(request, "Invalid graduation year. Please enter a year between 1900 and the current year.")
            return redirect('home')

        selected_category_slug = request.GET.get('category')
        categories = Category.objects.all()
        
        if not categories.exists():
            logger.warning("No categories found in the database.")
            messages.warning(request, "No categories are available at the moment. Please try again later.")
            return redirect('home')

        selected_category = None
        outdated_info = []
        relevant_info = []
        new_developments = []

        if selected_category_slug:
            try:
                selected_category = categories.get(slug=selected_category_slug)
                all_items = InformationItem.objects.filter(category=selected_category)
                
                outdated_info = all_items.filter(is_outdated=True, year__lte=grad_year)
                relevant_info = all_items.filter(is_outdated=False, year__lte=grad_year)
                new_developments = all_items.filter(year__gt=grad_year)
            except Category.DoesNotExist:
                logger.warning(f"Attempted to access non-existent category: {selected_category_slug}")
                messages.error(request, "The selected category does not exist.")
                return redirect('home')

        significant_events = SignificantEvent.objects.filter(year__gt=grad_year).order_by('year')
        recommended_books = Book.objects.filter(year__gt=grad_year, category=selected_category) if selected_category else []

        context = {
            'grad_year': grad_year,
            'current_year': current_year,
            'categories': categories,
            'selected_category': selected_category,
            'outdated_info': outdated_info,
            'relevant_info': relevant_info,
            'new_developments': new_developments,
            'significant_events': significant_events,
            'recommended_books': recommended_books,
        }

        return render(request, 'results.html', context)

    except ValidationError as ve:
        logger.error(f"Validation error in results view: {str(ve)}")
        messages.error(request, "An error occurred while processing your request. Please try again.")
        return redirect('home')
    except Exception as e:
        logger.error(f"Unexpected error in results view: {str(e)}")
        return render(request, '500.html', status=500)

@api_view(['GET'])
def api_changes(request):
    """
    API endpoint for fetching category-specific changes.

    This view handles requests for dynamically loading category data.
    It returns JSON data containing outdated information, relevant information,
    and new developments for a specific category and graduation year.

    Args:
        request (HttpRequest): The HTTP request object containing 'grad_year'
                               and 'category' as GET parameters.

    Returns:
        Response: JSON data with category information or an error message.
    """
    try:
        grad_year = request.GET.get('grad_year')
        category_slug = request.GET.get('category')

        if not grad_year or not category_slug:
            return Response({'error': 'Missing required parameters'}, status=400)

        try:
            grad_year = int(grad_year)
            current_year = timezone.now().year
            if not (1900 <= grad_year <= current_year):
                return Response({'error': 'Invalid graduation year'}, status=400)
        except ValueError:
            return Response({'error': 'Invalid graduation year format'}, status=400)

        try:
            category = Category.objects.get(slug=category_slug)
        except Category.DoesNotExist:
            return Response({'error': 'Category not found'}, status=404)

        all_items = InformationItem.objects.filter(category=category)
        
        outdated_info = all_items.filter(is_outdated=True, year__lte=grad_year)
        relevant_info = all_items.filter(is_outdated=False, year__lte=grad_year)
        new_developments = all_items.filter(year__gt=grad_year)

        data = {
            'category': CategorySerializer(category).data,
            'outdated_info': InformationItemSerializer(outdated_info, many=True).data,
            'relevant_info': InformationItemSerializer(relevant_info, many=True).data,
            'new_developments': InformationItemSerializer(new_developments, many=True).data,
        }

        return Response(data)

    except Exception as e:
        logger.error(f"Error in api_changes view: {str(e)}")
        return Response({'error': 'An unexpected error occurred'}, status=500)

@require_GET
def about(request):
    """
    Render the about page of the Nostalgia Site.

    This view displays information about the purpose and functionality
    of the Nostalgia Site.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Rendered about.html template.
    """
    try:
        return render(request, 'about.html')
    except Exception as e:
        logger.error(f"Error rendering about page: {str(e)}")
        return render(request, '500.html', status=500)

def error_404(request, exception):
    """
    Handle 404 (Page Not Found) errors.

    This view is called when a page is not found on the site.

    Args:
        request (HttpRequest): The HTTP request object.
        exception (Exception): The exception that was raised.

    Returns:
        HttpResponse: Rendered 404.html template with a 404 status code.
    """
    logger.warning(f"404 error: {request.path}")
    return render(request, '404.html', status=404)


def error_500(request):
    """
    Handle 500 (Internal Server Error) errors.

    This view is called when there's an internal server error.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Rendered 500.html template with a 500 status code.
    """
    logger.error(f"500 error occurred")
    return render(request, '500.html', status=500)