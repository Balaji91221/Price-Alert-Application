document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('login-form');
    const signupForm = document.getElementById('signup-form');

    loginForm.addEventListener('submit', function(event) {
        event.preventDefault();
        const formData = new FormData(loginForm);
        const data = {
            username: formData.get('username'),
            password: formData.get('password')
        };

        fetch('/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => {
            document.getElementById('login-message').textContent = data.message;
            if (data.access_token) {
                localStorage.setItem('access_token', data.access_token);
                document.getElementById('login-message').textContent = 'Login successful!';
                // Optionally redirect to another page
            }
        })
        .catch(error => console.error('Error:', error));
    });

    signupForm.addEventListener('submit', function(event) {
        event.preventDefault();
        const formData = new FormData(signupForm);
        const data = {
            username: formData.get('username'),
            password: formData.get('password'),
            email: formData.get('email')
        };

        fetch('/signup', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => {
            document.getElementById('signup-message').textContent = data.message;
            if (data.message === 'User signed up successfully') {
                document.getElementById('signup-message').textContent = 'Signup successful! You can now log in.';
            }
        })
        .catch(error => console.error('Error:', error));
    });
});
