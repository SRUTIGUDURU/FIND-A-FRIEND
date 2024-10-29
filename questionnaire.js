document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM fully loaded and parsed');

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

    async function storeData(data) {
        try {
            const response = await fetch('https://okmzzeoaqkllbzpyynnl.supabase.co', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9rbXp6ZW9hcWtsbGJ6cHl5bm5sIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzAxMzE5NzQsImV4cCI6MjA0NTcwNzk3NH0.hpmwUO2UozsTwm0g9cbCR4_Rgr_Go-vRHMPUfi582-g'
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

        // Handle multiple-value fields for hobbies and topics
        data.hobbies = formData.getAll('hobbies').join(', ');
        data.topics = formData.getAll('topics').join(', ');

        console.log('Collected form data:', data);

        if (await storeData(data)) {
            alert('Form data collected and stored successfully');
            window.location.href = 'dashboard.html'; // Redirect to the dashboard
        }
    });
});


