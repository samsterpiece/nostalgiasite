document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('factSubmissionForm');
    const wantNotificationRadios = document.querySelectorAll('input[name="want_notification"]');
    const notificationFields = document.querySelector('.notification-fields');

    function toggleNotificationFields() {
        const showFields = document.getElementById('notify_yes').checked;
        notificationFields.style.display = showFields ? 'block' : 'none';
    }

    wantNotificationRadios.forEach(radio => {
        radio.addEventListener('change', toggleNotificationFields);
    });

    toggleNotificationFields(); // Initial state

    form.addEventListener('submit', function(e) {
        e.preventDefault();

        const formData = new FormData(form);

        fetch(form.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': formData.get('csrfmiddlewaretoken')
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Fact submitted successfully!');
                form.reset();
                toggleNotificationFields(); // Reset notification fields visibility
            } else {
                let errorMessage = 'Error submitting fact:\n';
                for (const [key, value] of Object.entries(data.error)) {
                    errorMessage += `${key}: ${value.join(', ')}\n`;
                }
                alert(errorMessage);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while submitting the fact.');
        });
    });
});