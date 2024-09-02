import logging
import requests
import wikipedia
from bs4 import BeautifulSoup
from celery import shared_task
from django.db import transaction
from .helpers import fetch_open_library_books, cleanup_books_without_description
from .models import SignificantEvent, Book, Category

logger = logging.getLogger(__name__)
OPEN_LIBRARY_HEADERS = {
    "User-Agent": "NostalgiaSite/1.0 (nostalgiasite@proton.me)"
}

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def update_significant_events(self, year):
    """
    Update significant events for a given year.

    Args:
        self: The Celery task instance.
        year (int): The year to update events for.

    Returns:
        None
    """
    try:
        wiki_page = wikipedia.page(f"{year}")
        soup = BeautifulSoup(wiki_page.html(), 'html.parser')

        events_section = soup.find('span', {'id': 'Events'})
        if events_section:
            ul = events_section.find_next('ul')
            if ul:
                for li in ul.find_all('li', limit=10):
                    event_text = li.text.strip()
                    try:
                        event_page = wikipedia.page(event_text, auto_suggest=False)
                        event_url = event_page.url
                        event_impact = event_page.summary.split('.')[0]  # Get the first sentence as impact
                    except:
                        event_url = wiki_page.url
                        event_impact = "Impact information not available."

                    SignificantEvent.objects.get_or_create(
                        year=year,
                        title=event_text[:200],
                        defaults={
                            'description': event_text,
                            'source_url': event_url,
                            'impact': event_impact
                        }
                    )
        logger.info(f"Successfully updated significant events for {year}")
    except Exception as e:
        logger.error(f"Error updating significant events for {year}: {str(e)}")
        self.retry(exc=e)


@shared_task
def fetch_and_update_books(year, category_name='fiction'):
    """
    Fetch and update book records, ensuring URL updates and deletion of records with no description.
    """
    books = fetch_open_library_books(year, category_name, 10)
    with transaction.atomic():
        for book_data in books:
            if book_data['description']:
                book, created = Book.objects.update_or_create(
                    title=book_data['title'],
                    defaults=book_data  # Update all fields from book_data
                )
                logger.info(f"Updated/created book: {book.title}")
            else:
                Book.objects.filter(title=book_data['title']).delete()
                logger.info(f"Deleted book with no description: {book_data['title']}")

        logger.info(f"Books processing completed for year {year} and category {category_name}")