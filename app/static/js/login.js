
document.querySelector('form').addEventListener('submit', async (event) => {
    event.preventDefault(); // Evita el envío por defecto
    const form = event.target;

    const formData = new FormData(form);
    const data = new URLSearchParams(formData);

    try {
        const response = await fetch('/authenticate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: data
        });

        if (response.ok) {
            // Si el login es exitoso, redirige al usuario a /home
            window.location.href = '/home';
        } else {
            // Si ocurre un error, muestra el mensaje en la página
            const error = await response.json();
            const errorDiv = document.getElementById('error-message');
            errorDiv.textContent = error.detail || "Error desconocido";
            errorDiv.style.display = 'block';
        }
    } catch (error) {
        console.error('Error during login:', error);
        const errorDiv = document.getElementById('error-message');
        errorDiv.textContent = "Ocurrió un error al intentar iniciar sesión.";
        errorDiv.style.display = 'block';
    }
});

