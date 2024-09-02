document.addEventListener('DOMContentLoaded', function() {
    // Existing content handling code
    let activeCategory = null;
    const factsContainer = document.getElementById('facts-container');
    const loadingIndicator = document.getElementById('loading');
    const significantEventsList = document.getElementById('significant-events-list');
    const recommendedReadingList = document.getElementById('recommended-reading-list');
    const errorMessageContainer = document.getElementById('error-message');

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
        }).then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        }).then(data => {
            console.log('Received data:', data);
            showLoading(false);
            populateFacts(data.facts);
            populateSignificantEvents(data.significant_events);
            populateRecommendedReading(data.recommended_reading);
        }).catch(error => {
            console.error('Error:', error);
            showError(`Failed to fetch results: ${error.message}`);
            showLoading(false);
        });
    }

    // Code to manage form submission for submitting facts
    const form = document.getElementById('factSubmissionForm');
    const wantNotificationRadios = document.querySelectorAll('input[name="want_notification"]');
    const notificationFields = document.querySelector('.notification-fields');

    function toggleNotificationFields() {
        const showFields = document.getElementById('notify_yes').checked;
        notificationFields.style.display = showFields ? 'block' : 'none';
        console.log(`Notification fields display set to: ${notificationFields.style.display}`);
    }

    wantNotificationRadios.forEach(radio => {
        radio.addEventListener('change', toggleNotificationFields);
    });

    toggleNotificationFields(); // Initial state

    form.addEventListener('submit', function(e) {
        e.preventDefault();
        console.log('Form submission started.');

        const formData = new FormData(form);
        console.log('Form Data Collected:', Array.from(formData.entries()));

        fetch(form.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': formData.get('csrfmiddlewaretoken')
            }
        }).then(response => {
            console.log('Response received:', response);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        }).then(data => {
            console.log('Response data parsed:', data);
            if (data.success) {
                console.log('Submission successful, resetting form.');
                alert('Fact submitted successfully!');
                form.reset();
                toggleNotificationFields(); // Reset notification fields visibility
            } else {
                let errorMessage = 'Error submitting fact:\n';
                for (const [key, value] of Object.entries(data.error)) {
                    errorMessage += `${key}: ${value.join(', ')}\n`;
                }
                console.error('Submission errors:', errorMessage);
                alert(errorMessage);
            }
        }).catch(error => {
            console.error('Error in submission:', error);
            alert('An error occurred while submitting the fact.');
        });
    });
});