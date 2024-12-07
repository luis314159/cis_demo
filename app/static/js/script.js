const uploadForm = document.getElementById("uploadForm");
const fileInput = document.getElementById("fileInput");
const fileName = document.getElementById("fileName");
const notification = document.getElementById("notification");
const spinner = document.getElementById("spinner");

// Mostrar el nombre del archivo seleccionado
fileInput.addEventListener("change", () => {
    if (fileInput.files.length > 0) {
        fileName.textContent = `Archivo seleccionado: ${fileInput.files[0].name}`;
        fileName.classList.remove("hidden");
    } else {
        fileName.textContent = "Ningún archivo seleccionado";
        fileName.classList.add("hidden");
    }
});

uploadForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    if (!fileInput.files.length) {
        showNotification("Por favor, selecciona un archivo.", "error");
        return;
    }

    showSpinner();

    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append("file", file);

    try {
        const response = await fetch("http://localhost:8000/upload_csv/", {
            method: "POST",
            body: formData,
        });

        const result = await response.json();

        if (response.ok) {
            showNotification(`¡Archivo procesado con éxito! ${result.detail}`, "success");
        } else {
            showNotification(`Error: ${result.detail}`, "error");
        }
    } catch (error) {
        showNotification("Ocurrió un error al subir el archivo.", "error");
    } finally {
        hideSpinner();
    }
});

function showNotification(message, type) {
    notification.textContent = message;
    notification.className = `notification ${type}`;
    notification.classList.remove("hidden");

    setTimeout(() => {
        notification.classList.add("hidden");
    }, 5000);
}

function showSpinner() {
    spinner.classList.remove("hidden");
}

function hideSpinner() {
    spinner.classList.add("hidden");
}
