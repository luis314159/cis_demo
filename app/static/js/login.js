document.querySelector('form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = new URLSearchParams(formData);
    
    try {
        const response = await fetch('/authenticate', {
            method: 'POST',
            headers: {'Content-Type': 'application/x-www-form-urlencoded'},
            body: data
        });
        
        if (!response.ok) throw await response.json();
        window.location.href = '/home';
    } catch (error) {
        document.getElementById('error-message').textContent = 
            error.detail || "Error de autenticación";
    }
});