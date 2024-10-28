window.onload = function() {
    // Check if user is logged in
    const token = localStorage.getItem('access_token');
    if (!token) {
        window.location.href = 'index.html';
        return;
    }
    document.getElementById('signOutBtn').addEventListener('click', function() {
        // Sign out from Google
        google.accounts.id.disableAutoSelect();
        // Clear local storage
        localStorage.removeItem('access_token');
        // Redirect to the login page
        window.location.href = 'index.html';
    });
}