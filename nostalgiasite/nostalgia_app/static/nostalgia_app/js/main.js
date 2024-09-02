document.addEventListener('DOMContentLoaded', function() {
    let activeCategory = null;
    const factsContainer = document.getElementById('facts-container');
    const loadingIndicator = document.getElementById('loading');
    const significantEventsList = document.getElementById('significant-events-list');
    const recommendedReadingList = document.getElementById('recommended-reading-list');
    const errorMessageContainer = document.getElementById('error-message');

    // Check if grad_year is defined
    if (typeof grad_year === 'undefined') {
        console.error('grad_year is not defined');
        showError('An error occurred: graduation year is not defined.');
        return;
    }

    function showLoading(show) {
        loadingIndicator.style.display = show ? 'block' : 'none';
        factsContainer.style.display = show ? 'none' : 'block';
    }

    function showError(message) {
        console.error(message);
        errorMessageContainer.textContent = message;
        errorMessageContainer.style.display = 'block';
    }

    function fetchData(category = 'all') {
        showLoading(true);
        const timestamp = new Date().getTime();
        const url = `/api/results/${grad_year}/?category=${category}&timestamp=${timestamp}`;

        console.log(`Fetching data from: ${url}`);

        fetch(url, {
            headers: {
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache'
            }
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('Received data:', data);
                showLoading(false);
                populateFacts(data.facts);
                populateSignificantEvents(data.significant_events);
                populateRecommendedReading(data.recommended_reading);
            })
            .catch(error => {
                console.error('Error:', error);
                showError(`Failed to fetch results: ${error.message}`);
                showLoading(false);
            });
    }

    function populateFacts(facts) {
        console.log('Populating facts:', facts);
        factsContainer.innerHTML = '';
        if (!facts || facts.length === 0) {
            factsContainer.innerHTML = '<p>No facts available for the selected category and time period.</p>';
            return;
        }

        facts.forEach(fact => {
            const factItem = document.createElement('div');
            factItem.classList.add('fact-item');
            factItem.innerHTML = `
                <h4>${fact.year} - ${fact.title}</h4>
                <p>${fact.description}</p>
                <a href="${fact.source_url}" target="_blank" rel="noopener noreferrer">Learn More</a>
            `;
            factsContainer.appendChild(factItem);
        });
    }

    function populateSignificantEvents(events) {
        console.log('Populating significant events:', events);
        significantEventsList.innerHTML = '';
        if (!events || events.length === 0) {
            significantEventsList.innerHTML = '<p>No significant events available for this time period.</p>';
            return;
        }

        events.forEach(event => {
            const eventItem = document.createElement('div');
            eventItem.classList.add('event-item');
            eventItem.innerHTML = `
                <h4>${event.year} - ${event.title}</h4>
                <p>${event.description}</p>
                <a href="${event.source_url}" target="_blank" rel="noopener noreferrer">Learn More</a>
            `;
            significantEventsList.appendChild(eventItem);
        });
    }

    function populateRecommendedReading(books) {
        console.log('Populating recommended reading:', books);
        recommendedReadingList.innerHTML = '';
        if (!books || books.length === 0) {
            recommendedReadingList.innerHTML = '<p>No reading recommendations available for this time period.</p>';
            return;
        }

        books.forEach(book => {
            const bookItem = document.createElement('div');
            bookItem.classList.add('book-item');
            bookItem.innerHTML = `
                <h4>${book.title}</h4>
                <p>By ${book.author}</p>
                <p>${book.description || 'No description available.'}</p>
                <p>Categories: ${book.categories ? book.categories.join(', ') : 'Not categorized'}</p>
                ${book.cover_url ? `<img src="${book.cover_url}" alt="Book cover" style="max-width: 100px;">` : ''}
                <a href="${book.source_url}" target="_blank" rel="noopener noreferrer">Learn More</a>
            `;
            recommendedReadingList.appendChild(bookItem);
        });
    }

    // Set up event listeners for category buttons
    document.querySelectorAll('.category-button').forEach(button => {
        button.addEventListener('click', function() {
            if (activeCategory) {
                activeCategory.classList.remove('active');
            }
            this.classList.add('active');
            activeCategory = this;
            fetchData(this.dataset.category);
        });
    });

    // Initial data fetch
    fetchData();
});