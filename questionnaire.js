import { createClient } from '@supabase/supabase-js';

// Initialize Supabase client
const supabaseUrl = 'https://okmzzeoaqkllbzpyynnl.supabase.co'; // Replace with your Supabase URL
const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9rbXp6ZW9hcWtsbGJ6cHl5bm5sIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzAxMzE5NzQsImV4cCI6MjA0NTcwNzk3NH0.hpmwUO2UozsTwm0g9cbCR4_Rgr_Go-vRHMPUfi582-g'; // Replace with your Supabase API key
const supabase = createClient(supabaseUrl, supabaseKey);

document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM fully loaded and parsed');

    // Define the list of hobbies and topics
    const hobbiesList = [
        "coding", "reading", "watching stuff", "crocheting", "drawing/painting",
        "singing", "writing", "musical instruments", "tennis", "football", "basketball", "badminton",
        "squash", "volleyball", "throwball"
    ];

    const topicsList = [
        "fashion", "clubs/departments", "politics", "pop culture", "world wars",
        "history", "cricket", "Football (as a topic)", "current affairs"
    ];

    // Locate the container elements for checkboxes
    const hobbiesContainer = document.getElementById('hobbies-container');
    const topicsContainer = document.getElementById('topics-container');

    // Check if containers exist
    if (!hobbiesContainer || !topicsContainer) {
        console.error('Checkbox container elements not found');
        return;
    }

    // Function to create checkboxes for hobbies and topics
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

    // Create checkboxes for both hobbies and topics
    createCheckboxes(hobbiesContainer, hobbiesList, 'hobbies');
    createCheckboxes(topicsContainer, topicsList, 'topics');

    // Form submission handling
    document.getElementById('questionnaireForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Collect form data
        const formData = new FormData(this);
        const data = Object.fromEntries(formData.entries());
        
        // Collect all selected hobbies and topics
        data.hobbies = formData.getAll('hobbies').join(', ');
        data.topics = formData.getAll('topics').join(', ');

        console.log('Collected form data:', data);

        // Get user email from session (you can replace this with your actual user fetching logic)
        const user = supabase.auth.user();
        if (user) {
            data.email = user.email;

            // Check if an entry already exists for this user
            const { data: existingData, error: fetchError } = await supabase
                .from('questionnaire')
                .select('*')
                .eq('email', user.email)
                .single();

            if (fetchError) {
                console.error('Error fetching existing data:', fetchError);
                return;
            }

            if (existingData) {
                // Update existing entry
                const { error: updateError } = await supabase
                    .from('questionnaire')
                    .update(data)
                    .eq('id', existingData.id);

                if (updateError) {
                    console.error('Error updating data:', updateError);
                } else {
                    alert('Questionnaire updated successfully!');
                }
            } else {
                // Insert new entry
                const { error: insertError } = await supabase
                    .from('questionnaire')
                    .insert([data]);

                if (insertError) {
                    console.error('Error inserting data:', insertError);
                } else {
                    alert('Questionnaire submitted successfully!');
                }
            }
        } else {
            console.error('No user is signed in.');
            alert('Please sign in to complete the questionnaire.');
        }

        // Redirect to dashboard (if needed)
        window.location.href = 'dashboard.html';
    });
});
