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
        
        if (!response.ok) {
            // Si la respuesta no es OK, procesamos el error como JSON
            const errorData = await response.json();
            const errorDiv = document.getElementById('error-message');
            errorDiv.textContent = errorData.detail || "Error de autenticación";
            errorDiv.className = 'alert alert-danger mt-3'; // Aseguramos que tenga las clases correctas
            errorDiv.style.display = 'block';
            throw errorData;
        }
        
        // Si la autenticación fue exitosa, redirigimos inmediatamente como antes
        window.location.href = '/home';
        
    } catch (error) {
        // Si hay un error en el fetch o al procesar la respuesta
        const errorDiv = document.getElementById('error-message');
        errorDiv.textContent = error.detail || "Error de autenticación";
        errorDiv.className = 'alert alert-danger mt-3';
        errorDiv.style.display = 'block';
    }
});