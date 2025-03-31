const uploadForm = document.getElementById("uploadForm");
const fileInput = document.getElementById("fileInput");
const fileName = document.getElementById("fileName");
const notification = document.getElementById("notification");
const spinner = document.getElementById("spinner");
const productSelect = document.getElementById("productSelect");

// Cargar productos cuando se carga la página
document.addEventListener("DOMContentLoaded", async () => {
    try {
        showSpinner();
        // Corregido: URL del endpoint debe ser "/object/products" según el router definido
        const response = await fetch("/products/products");
        
        if (response.ok) {
            const products = await response.json();
            
            // Limpiar opciones anteriores
            productSelect.innerHTML = '<option value="" selected disabled>-- Seleccione un producto --</option>';
            
            // Agregar productos al selector
            products.forEach(product => {
                const option = document.createElement("option");
                option.value = product.product_id;
                option.textContent = product.product_name;
                productSelect.appendChild(option);
            });
        } else {
            showNotification("Error al cargar los productos.", "error");
        }
    } catch (error) {
        showNotification("No se pudieron cargar los productos.", "error");
        console.error("Error loading products:", error);
    } finally {
        hideSpinner();
    }
});

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

    // Validar selección de producto
    const selectedProduct = productSelect.value;
    const selectedProductText = productSelect.options[productSelect.selectedIndex].text;
    
    if (!selectedProduct) {
        showNotification("Por favor, selecciona un producto.", "error");
        return;
    }

    // Validar selección de archivo
    if (!fileInput.files.length) {
        showNotification("Por favor, selecciona un archivo.", "error");
        return;
    }

    showSpinner();

    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append("file", file);
    // Ya no agregamos product_name al FormData porque lo enviaremos como query parameter

    try {
        console.log("Enviando datos: ", {
            file: fileInput.files[0].name,
            product_name: selectedProductText
        });
        
        // Agregamos el product_name como query parameter en la URL en lugar de en el FormData
        const response = await fetch(`/object/validate-and-insert?product_name=${encodeURIComponent(selectedProductText)}`, {
            method: "POST",
            body: formData,
        });

        if (!response.ok) {
            // Si hay un error, vamos a intentar obtener más detalles
            try {
                const errorData = await response.json();
                showNotification(`Error: ${JSON.stringify(errorData)}`, "error");
                console.error("Error detallado:", errorData);
            } catch (jsonError) {
                showNotification(`Error ${response.status}: ${response.statusText}`, "error");
                console.error("Estado de respuesta:", response.status, response.statusText);
            }
            return;
        }

        const result = await response.json();

        if (response.ok) {
            showNotification(`¡Archivo procesado con éxito! ${result.detail}`, "success");
            // Opcional: reiniciar el formulario después de un envío exitoso
            uploadForm.reset();
            fileName.textContent = "Ningún archivo seleccionado";
            fileName.classList.add("hidden");
        } else {
            showNotification(`Error: ${result.detail}`, "error");
        }
    } catch (error) {
        showNotification("Ocurrió un error al subir el archivo.", "error");
        console.error("Upload error:", error);
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