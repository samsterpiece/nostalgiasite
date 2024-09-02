import logging
from linecache import cache

import wikipedia
import requests

from .banned_authors import BANNED_AUTHORS
from .models import Category, APIFact, Book

logger = logging.getLogger(__name__)
OPEN_LIBRARY_HEADERS = {
    "User-Agent": "NostalgiaSite/1.0 (nostalgiasite@proton.me)"
}

def fetch_wikipedia_events(year, limit):
    """
    Fetch events from Wikipedia for a given year.

    Args:
        year (int): The year to fetch events for.
        limit (int): The maximum number of events to fetch.

    Returns:
        list: A list of dictionaries containing event information.
    """
    events = []
    try:
        search_results = wikipedia.search(f"{year} events", results=limit)
        for result in search_results:
            try:
                page = wikipedia.page(result, auto_suggest=False)
                summary = page.summary.split('. ')[0]
                events.append({'title': result, 'description': summary, 'source_url': page.url})
            except (wikipedia.exceptions.DisambiguationError, wikipedia.exceptions.PageError):
                continue
    except Exception as e:
        logger.error(f"Error fetching Wikipedia events for {year}: {str(e)}")
    return events


def fetch_open_library_books(year, category_name, limit):
    """
    Fetch books from Open Library for a given year and category, enriching them with Wikipedia descriptions and excluding books with blank descriptions.

    Args:
        year (int): The year to fetch books for.
        category_name (str): The category of books to fetch.
        limit (int): The maximum number of books to fetch.

    Returns:
        list: A list of dictionaries containing book information, excluding those with blank descriptions.
    """
    books = []
    try:
        url = f"http://openlibrary.org/subjects/{category_name.lower().replace(' ', '_')}.json?published_in={year}"
        response = requests.get(url, headers=OPEN_LIBRARY_HEADERS)
        data = response.json()

        for work in data.get('works', [])[:limit]:
            title = work.get('title', 'Unknown Title')
            authors = ', '.join([author.get('name', 'Unknown Author') for author in work.get('authors', [])])
            if any(author in BANNED_AUTHORS for author in authors):
                continue #Skip this book if author is in banned list

            book_info = fetch_book_description(title, authors)
            description = book_info.get("description")
            book_url = book_info.get("url")
            if description:  # Ensure description is not blank
                books.append({
                    'title': title,
                    'author': authors,
                    'description': description,
                    'source_url': book_url,
                    'cover_url': f"https://covers.openlibrary.org/b/id/{work.get('cover_id')}-M.jpg",
                    'categories': [subject.capitalize() for subject in work.get('subject', [])]
                })
            else:
                logger.info(f"Excluded book '{title}' due to blank description.")
    except Exception as e:
        logger.error(f"Error fetching Open Library books for {year} and category {category_name}: {str(e)}")
    return books


def fetch_book_description(title, authors):
    """
    Attempt to fetch a detailed description and the URL of a book from Wikipedia.

    Args:
        title (str): The book title.
        authors (str): The book authors.

    Returns:
        dict: Contains 'description' and 'url'. If no valid page is found, both fields are None.
    """
    search_query = f"{title} book by {authors}"
    try:
        search_results = wikipedia.search(search_query, results=5)
        for result in search_results:
            try:
                page = wikipedia.page(result, auto_suggest=False)
                if title.lower() in page.title.lower():
                    summary = '. '.join(page.summary.split('. ')[:2]) + '.'
                    return {"description": summary, "url": page.url}
            except wikipedia.exceptions.PageError:
                continue
        return {"description": None, "url": None}
    except Exception as e:
        logger.error(f"Error fetching description for '{title}': {str(e)}")
        return {"description": None, "url": None}



def fetch_api_facts(grad_year):
    """
    Fetch API facts for a given graduation year.

    Args:
        grad_year (int): The graduation year to fetch facts for.

    Returns:
        list: A list of APIFact objects.
    """
    cache_key = f'api_facts_{grad_year}'
    cached_facts = cache.get(cache_key)

    if cached_facts:
        return cached_facts

    facts = []
    try:
        for category in Category.objects.all():
            search_query = f"{grad_year} {category.name}"
            search_results = wikipedia.search(search_query, results=5)

            for result in search_results:
                try:
                    page = wikipedia.page(result, auto_suggest=False)

                    if str(grad_year) in page.title or str(grad_year) in page.content[:500]:
                        summary = page.summary.split('. ')[0].strip()

                        if str(grad_year) not in summary:
                            summary = f"In {grad_year}, " + summary

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
                        facts.append(fact)
                        break
                except (wikipedia.exceptions.DisambiguationError, wikipedia.exceptions.PageError):
                    continue
    except Exception as e:
        logger.error(f"Error fetching API facts for {grad_year}: {str(e)}")

    cache.set(cache_key, facts, 86400)  # Cache for 24 hours
    return facts

def cleanup_books_without_description():
    """
    Removes books from the database that do not have a description (blank field).
    """
    # Query to find books with blank descriptions
    no_desc_count, _ = Book.objects.filter(description="").delete()
    logger.info(f"Removed {no_desc_count} books without descriptions from the database.")