document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM fully loaded and parsed');

    // Hobby and Topic Lists
    const hobbiesList = [
        "coding", "reading", "watching stuff", "crocheting", "drawing/painting",
        "singing", "writing", "musical instruments", "tennis", "football", "basketball", "badminton",
        "squash", "volleyball", "throwball"
    ];

    const topicsList = [
        "fashion", "clubs/departments", "politics", "pop culture", "world wars",
        "history", "cricket", "Football (as a topic)", "current affairs"
    ];

    const hobbiesContainer = document.getElementById('hobbies-container');
    const topicsContainer = document.getElementById('topics-container');

    if (!hobbiesContainer || !topicsContainer) {
        console.error('Checkbox container elements not found');
        return;
    }

    function createCheckboxes(container, items, name) {
        items.forEach(item => {
            const div = document.createElement('div');
            div.className = 'checkbox-group';
            div.innerHTML = `
                <input type="checkbox" id="${item}" name="${name}" value="${item}">
                <label for="${item}">${item}</label>
            `;
            container.appendChild(div);
        });
        console.log(`Checkboxes created for ${name}`);
    }

    createCheckboxes(hobbiesContainer, hobbiesList, 'hobbies');
    createCheckboxes(topicsContainer, topicsList, 'topics');

    const SUPABASE_URL = 'https://okmzzeoaqkllbzpyynnl.supabase.co/rest/v1/questionnaire';
    const SUPABASE_API_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9rbXp6ZW9hcWtsbGJ6cHl5bm5sIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzAxMzE5NzQsImV4cCI6MjA0NTcwNzk3NH0.hpmwUO2UozsTwm0g9cbCR4_Rgr_Go-vRHMPUfi582-g';

    async function deleteExistingSubmission(email) {
        try {
            const response = await fetch(`${SUPABASE_URL}?email=eq.${email}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                    'apikey': SUPABASE_API_KEY,
                    'Authorization': `Bearer ${SUPABASE_API_KEY}`
                }
            });
            if (!response.ok) throw new Error('Failed to delete existing submission');
            console.log('Previous submission deleted');
        } catch (error) {
            console.error('Error deleting existing submission:', error);
        }
    }

    async function storeData(data) {
        try {
            // Check if a submission by this user already exists
            await deleteExistingSubmission(data.email);

            // Insert new submission
            const response = await fetch(SUPABASE_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'apikey': SUPABASE_API_KEY,
                    'Authorization': `Bearer ${SUPABASE_API_KEY}`
                },
                body: JSON.stringify(data)
            });

            if (!response.ok) throw new Error('Failed to store data');
            console.log('Data successfully stored');
        } catch (error) {
            console.error('Error storing data:', error);
            alert('Failed to store data. Please try again.');
            return false;
        }
        return true;
    }

    document.getElementById('questionnaireForm').addEventListener('submit', async function(e) {
        e.preventDefault();

        const formData = new FormData(this);
        const data = Object.fromEntries(formData.entries());

        // Retrieve email from localStorage and include it in data
        const email = localStorage.getItem('userEmail');
        if (!email) {
            alert('User email not found. Please sign in again.');
            return;
        }
        data.email = email;

        data.hobbies = formData.getAll('hobbies').join(', ');
        data.topics = formData.getAll('topics').join(', ');

        console.log('Collected form data:', data);

        if (await storeData(data)) {
            alert('Form data collected and stored successfully');
            window.location.assign('dashboard.html');
        }
    });
});
