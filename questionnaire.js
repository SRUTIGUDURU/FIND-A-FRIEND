<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Questionnaire</title>
</head>
<body>
    <form id="questionnaireForm">
        <div id="hobbies-container"></div>
        <div id="topics-container"></div>
        <button type="submit">Submit</button>
    </form>

    <script type="module">
        import { createClient } from '@supabase/supabase-js';

        const supabaseUrl = 'https://okmzzeoaqkllbzpyynnl.supabase.co';
        const supabaseKey = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9rbXp6ZW9hcWtsbGJ6cHl5bm5sIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzAxMzE5NzQsImV4cCI6MjA0NTcwNzk3NH0.hpmwUO2UozsTwm0g9cbCR4_Rgr_Go-vRHMPUfi582-g";
        const supabase = createClient(supabaseUrl, supabaseKey);

        // Define hobby and topic lists
        const hobbiesList = [
            "coding", "reading", "watching stuff", "crocheting", "drawing/painting",
            "singing", "writing", "tennis", "football", "basketball", "badminton",
            "squash", "volleyball", "throwball", "musical instruments"
        ];
        const topicsList = [
            "fashion", "clubs/departments", "politics", "pop culture", "world wars",
            "history", "cricket", "Football (as a topic)", "current affairs"
        ];

        document.addEventListener('DOMContentLoaded', () => {
            // Create checkboxes for hobbies and topics
            const hobbiesContainer = document.getElementById('hobbies-container');
            const topicsContainer = document.getElementById('topics-container');

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
            }

            createCheckboxes(hobbiesContainer, hobbiesList, 'hobbies');
            createCheckboxes(topicsContainer, topicsList, 'topics');

            // Form submission handling
            document.getElementById('questionnaireForm').addEventListener('submit', async function(e) {
                e.preventDefault();
                
                const formData = new FormData(this);
                const data = Object.fromEntries(formData.entries());
                
                // Handle multiple selections for hobbies and topics
                data.hobbies = formData.getAll('hobbies').join(', ');
                data.topics = formData.getAll('topics').join(', ');

                // Get user email from session
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
            });
        });
    </script>
</body>
</html>
