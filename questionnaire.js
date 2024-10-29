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

    document.getElementById('questionnaireForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        const formData = new FormData(this);
        const data = Object.fromEntries(formData.entries());

        data.hobbies = formData.getAll('hobbies').join(', ');
        data.topics = formData.getAll('topics').join(', ');

        console.log('Collected form data:', data);
        alert('Form data collected successfully');
    });
});
