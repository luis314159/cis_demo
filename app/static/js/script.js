// Variables globales
let products = [];
let jobCodes = [];
let defectData = [];
let selectedProduct = '';
let selectedJobCode = '';
let currentDefectIndex = -1;
let statuses = [];
let correctionProcesses = [];

// Cargar los productos al iniciar la página
document.addEventListener('DOMContentLoaded', () => {
    loadProducts();
    loadStatuses();
    loadCorrectionProcesses();
    
    // Configurar event listeners
    document.getElementById('productSelector').addEventListener('change', handleProductChange);
    document.getElementById('jobCodeSelector').addEventListener('change', handleJobCodeChange);
    document.getElementById('editDefectForm').addEventListener('submit', handleDefectFormSubmit);
});

// Función para cargar productos desde la API
async function loadProducts() {
    try {
        const response = await fetch('/products');
        if (!response.ok) {
            throw new Error('Error al cargar los productos');
        }
        products = await response.json();
        renderProducts(products);
    } catch (error) {
        console.error('Error:', error);
        alert('No se pudieron cargar los productos. Por favor, intente de nuevo más tarde.');
    }
}

// Función para cargar los estados disponibles
async function loadStatuses() {
    try {
        const response = await fetch('/status');
        if (!response.ok) {
            throw new Error('Error al cargar los estados');
        }
        statuses = await response.json();
    } catch (error) {
        console.error('Error:', error);
        alert('No se pudieron cargar los estados. Por favor, intente de nuevo más tarde.');
    }
}

// Función para cargar los procesos de corrección disponibles
async function loadCorrectionProcesses() {
    try {
        const response = await fetch('/correction-processes');
        if (!response.ok) {
            throw new Error('Error al cargar los procesos de corrección');
        }
        correctionProcesses = await response.json();
    } catch (error) {
        console.error('Error:', error);
        alert('No se pudieron cargar los procesos de corrección. Por favor, intente de nuevo más tarde.');
    }
}

// Función para renderizar los productos en el selector
function renderProducts(products) {
    const productSelector = document.getElementById('productSelector');
    const defaultOption = productSelector.querySelector('option');
    
    productSelector.innerHTML = '';
    productSelector.appendChild(defaultOption);
    
    products.forEach(product => {
        const option = document.createElement('option');
        option.value = product.product_name;
        option.textContent = product.product_name;
        productSelector.appendChild(option);
    });
}

// Función para manejar el cambio de producto
async function handleProductChange(event) {
    selectedProduct = event.target.value;
    
    if (!selectedProduct) {
        document.getElementById('jobCodeContainer').classList.add('hidden');
        document.getElementById('defectsContainer').classList.add('hidden');
        document.getElementById('noDataMessage').classList.add('hidden');
        return;
    }
    
    try {
        const response = await fetch(`/jobs/list-by-product/${selectedProduct}`);
        if (!response.ok) {
            throw new Error('Error al cargar los job codes');
        }
        jobCodes = await response.json();
        renderJobCodes(jobCodes);
        
        document.getElementById('jobCodeContainer').classList.remove('hidden');
        document.getElementById('defectsContainer').classList.add('hidden');
        document.getElementById('noDataMessage').classList.add('hidden');
    } catch (error) {
        console.error('Error:', error);
        alert('No se pudieron cargar los job codes. Por favor, intente de nuevo más tarde.');
    }
}

// Función para renderizar los job codes en el selector
function renderJobCodes(jobCodes) {
    const jobCodeSelector = document.getElementById('jobCodeSelector');
    const defaultOption = jobCodeSelector.querySelector('option');
    
    jobCodeSelector.innerHTML = '';
    jobCodeSelector.appendChild(defaultOption);
    
    jobCodes.forEach(job => {
        const option = document.createElement('option');
        option.value = job.job_code;
        option.textContent = job.job_code;
        jobCodeSelector.appendChild(option);
    });
}

// Función para manejar el cambio de job code
async function handleJobCodeChange(event) {
    selectedJobCode = event.target.value;
    
    if (!selectedJobCode || !selectedProduct) {
        document.getElementById('defectsContainer').classList.add('hidden');
        document.getElementById('noDataMessage').classList.add('hidden');
        return;
    }
    
    try {
        // Usar el endpoint actualizado
        const response = await fetch(`/defect-records/complete/${selectedJobCode}/${selectedProduct}`);
        if (!response.ok) {
            throw new Error('Error al cargar los datos de defectos');
        }
        defectData = await response.json();
        
        if (defectData.length === 0) {
            document.getElementById('defectsContainer').classList.add('hidden');
            document.getElementById('noDataMessage').classList.remove('hidden');
        } else {
            renderDefects(defectData);
            document.getElementById('defectsContainer').classList.remove('hidden');
            document.getElementById('noDataMessage').classList.add('hidden');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('No se pudieron cargar los datos de defectos. Por favor, intente de nuevo más tarde.');
    }
}

// Función para renderizar los defectos en la tabla
function renderDefects(defects) {
    const tableBody = document.getElementById('defectsTableBody');
    tableBody.innerHTML = '';
    
    defects.forEach((defect, index) => {
        const row = document.createElement('tr');
        
        // Formatear fechas
        const dateOpened = new Date(defect.date_opened).toLocaleDateString();
        const dateClosed = defect.date_closed ? new Date(defect.date_closed).toLocaleDateString() : '-';
        
        row.innerHTML = `
            <td class="px-6 py-4 whitespace-nowrap">${dateOpened}</td>
            <td class="px-6 py-4 whitespace-nowrap">${dateClosed}</td>
            <td class="px-6 py-4 whitespace-nowrap">${defect.inspector?.employee_number || '-'}</td>
            <td class="px-6 py-4 whitespace-nowrap">${defect.issue_by_user?.employee_number || '-'}</td>
            <td class="px-6 py-4 whitespace-nowrap">
                <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full 
                    ${defect.status?.status_name === 'Ok' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}">
                    ${defect.status?.status_name || 'N/A'}
                </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
                <div class="flex space-x-2">
                    ${defect.images && defect.images.slice(0, 3).map((image, imgIndex) => `
                        <img src="${image.image_url}" alt="Defecto ${imgIndex + 1}" 
                            class="h-16 w-16 object-cover rounded defect-image" 
                            onclick="showFullImage(event, '${image.image_url}')">
                    `).join('')}
                    ${defect.images && defect.images.length > 3 ? `<span class="text-blue-500">+${defect.images.length - 3} más</span>` : ''}
                </div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
                <button 
                    class="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600"
                    onclick="showDefectDetails(${index})">
                    Ver
                </button>
                <button 
                    class="px-3 py-1 ml-2 bg-yellow-500 text-white rounded hover:bg-yellow-600"
                    onclick="openEditModal(${index})">
                    Editar
                </button>
            </td>
        `;
        
        tableBody.appendChild(row);
    });
}

// Función para mostrar imagen ampliada
function showFullImage(event, imageSrc) {
    event.stopPropagation(); // Evitar que se active el evento de la fila
    
    document.getElementById('enlargedImage').src = imageSrc;
    document.getElementById('imageModal').classList.remove('hidden');
}

// Función para cerrar el modal de imagen
function closeImageModal() {
    document.getElementById('imageModal').classList.add('hidden');
}

// Función para mostrar detalles del defecto
function showDefectDetails(index) {
    currentDefectIndex = index;
    const defect = defectData[index];
    const detailContent = document.getElementById('defectDetailContent');
    
    // Formatear fechas
    const dateOpened = new Date(defect.date_opened).toLocaleDateString();
    const dateClosed = defect.date_closed ? new Date(defect.date_closed).toLocaleDateString() : '-';
    
    detailContent.innerHTML = `
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="space-y-4">
                <div>
                    <h3 class="text-lg font-medium text-gray-900">Información General</h3>
                    <div class="mt-2 border-t border-gray-200 pt-2">
                        <dl class="divide-y divide-gray-200">
                            <div class="py-2 grid grid-cols-3 gap-4">
                                <dt class="text-sm font-medium text-gray-500">Producto:</dt>
                                <dd class="text-sm text-gray-900 col-span-2">${defect.product?.product_name || '-'}</dd>
                            </div>
                            <div class="py-2 grid grid-cols-3 gap-4">
                                <dt class="text-sm font-medium text-gray-500">Estado:</dt>
                                <dd class="text-sm text-gray-900 col-span-2">
                                    <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full 
                                        ${defect.status?.status_name === 'Ok' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}">
                                        ${defect.status?.status_name || 'N/A'}
                                    </span>
                                </dd>
                            </div>
                            <div class="py-2 grid grid-cols-3 gap-4">
                                <dt class="text-sm font-medium text-gray-500">Fecha Apertura:</dt>
                                <dd class="text-sm text-gray-900 col-span-2">${dateOpened}</dd>
                            </div>
                            <div class="py-2 grid grid-cols-3 gap-4">
                                <dt class="text-sm font-medium text-gray-500">Fecha Cierre:</dt>
                                <dd class="text-sm text-gray-900 col-span-2">${dateClosed}</dd>
                            </div>
                            ${defect.description ? `
                            <div class="py-2 grid grid-cols-3 gap-4">
                                <dt class="text-sm font-medium text-gray-500">Descripción:</dt>
                                <dd class="text-sm text-gray-900 col-span-2">${defect.description}</dd>
                            </div>
                            ` : ''}
                        </dl>
                    </div>
                </div>
                
                <div>
                    <h3 class="text-lg font-medium text-gray-900">Inspector</h3>
                    <div class="mt-2 border-t border-gray-200 pt-2">
                        <dl class="divide-y divide-gray-200">
                            <div class="py-2 grid grid-cols-3 gap-4">
                                <dt class="text-sm font-medium text-gray-500">Número de Empleado:</dt>
                                <dd class="text-sm text-gray-900 col-span-2">${defect.inspector?.employee_number || '-'}</dd>
                            </div>
                            <div class="py-2 grid grid-cols-3 gap-4">
                                <dt class="text-sm font-medium text-gray-500">Nombre Completo:</dt>
                                <dd class="text-sm text-gray-900 col-span-2">${defect.inspector?.first_name || '-'} ${defect.inspector?.first_surname || ''}</dd>
                            </div>
                            <div class="py-2 grid grid-cols-3 gap-4">
                                <dt class="text-sm font-medium text-gray-500">Rol:</dt>
                                <dd class="text-sm text-gray-900 col-span-2">${defect.inspector?.role?.role_name || '-'}</dd>
                            </div>
                        </dl>
                    </div>
                </div>
                
                <div>
                    <h3 class="text-lg font-medium text-gray-900">Error del usuario</h3>
                    <div class="mt-2 border-t border-gray-200 pt-2">
                        <dl class="divide-y divide-gray-200">
                            <div class="py-2 grid grid-cols-3 gap-4">
                                <dt class="text-sm font-medium text-gray-500">Número de Empleado:</dt>
                                <dd class="text-sm text-gray-900 col-span-2">${defect.issue_by_user?.employee_number || '-'}</dd>
                            </div>
                            <div class="py-2 grid grid-cols-3 gap-4">
                                <dt class="text-sm font-medium text-gray-500">Nombre Completo:</dt>
                                <dd class="text-sm text-gray-900 col-span-2">${defect.issue_by_user?.first_name || '-'} ${defect.issue_by_user?.first_surname || ''}</dd>
                            </div>
                            <div class="py-2 grid grid-cols-3 gap-4">
                                <dt class="text-sm font-medium text-gray-500">Rol:</dt>
                                <dd class="text-sm text-gray-900 col-span-2">${defect.issue_by_user?.role?.role_name || '-'}</dd>
                            </div>
                        </dl>
                    </div>
                </div>
            </div>
            
            <div>
                <h3 class="text-lg font-medium text-gray-900 mb-3">Imágenes</h3>
                <div class="grid grid-cols-1 gap-4">
                    ${defect.images && defect.images.map((image, imgIndex) => `
                        <div class="border rounded-lg overflow-hidden">
                            <img src="${image.image_url}" alt="Defecto ${imgIndex + 1}" 
                                class="w-full h-auto object-contain cursor-pointer" 
                                onclick="showFullImage(event, '${image.image_url}')">
                            <div class="p-2 bg-gray-50">
                                <p class="text-sm text-gray-500">${getImageTypeLabel(image)}</p>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        </div>
    `;
    
    document.getElementById('defectDetailModal').classList.remove('hidden');
}

// Función para obtener el tipo de imagen basado en la URL
function getImageTypeLabel(image) {
    // Verificar primero por image_type_id si está disponible
    if (image.image_type_id === 1) {
        return 'Solución implementada';
    } else if (image.image_type_id === 2) {
        return 'Ubicación del defecto';
    } else if (image.image_type_id === 3) {
        return 'Imagen del defecto';
    }

    // Si no hay image_type_id, intentar deducir por URL
    const imageUrl = image.image_url.toLowerCase();
    if (imageUrl.includes('solved')) {
        return 'Solución implementada';
    } else if (imageUrl.includes('location')) {
        return 'Ubicación del defecto';
    } else if (imageUrl.includes('defect')) {
        return 'Imagen del defecto';
    }
    return 'Imagen';
}

// Función para cerrar el modal de detalles
function closeDefectDetailModal() {
    document.getElementById('defectDetailModal').classList.add('hidden');
}

// Función para abrir el modal de edición
function openEditModal(index = null) {
    if (index !== null) {
        currentDefectIndex = index;
    }
    
    if (currentDefectIndex === -1) {
        alert('No se ha seleccionado ningún defecto para editar.');
        return;
    }
    
    const defect = defectData[currentDefectIndex];
    
    // Llenar el formulario con los datos del defecto
    document.getElementById('editDefectId').value = defect.defect_record_id;
    document.getElementById('editDescription').value = defect.description || '';
    
    // Poblar el selector de estados
    const statusSelector = document.getElementById('editStatus');
    statusSelector.innerHTML = '';
    statuses.forEach(status => {
        const option = document.createElement('option');
        option.value = status.status_id;
        option.textContent = status.status_name;
        if (defect.status && status.status_id === defect.status.status_id) {
            option.selected = true;
        }
        statusSelector.appendChild(option);
    });
    
    // Poblar el selector de procesos de corrección
    const cpSelector = document.getElementById('editCorrectionProcess');
    cpSelector.innerHTML = '';
    correctionProcesses.forEach(cp => {
        const option = document.createElement('option');
        option.value = cp.correction_process_id;
        option.textContent = cp.process_name;
        if (defect.correction_process && cp.correction_process_id === defect.correction_process.correction_process_id) {
            option.selected = true;
        }
        cpSelector.appendChild(option);
    });
    
    // Mostrar imágenes existentes
    displayExistingImages(defect);
    
    // Si el defecto ya está cerrado, marcar la casilla
    document.getElementById('closeRecord').checked = !!defect.date_closed;
    
    // Verificar si el estado seleccionado es "Ok" y mostrar un mensaje
    const currentStatus = defect.status?.status_id;
    const okStatusId = statuses.find(s => s.status_name === 'Ok')?.status_id;
    
    if (okStatusId) {
        const statusHelpText = document.getElementById('statusHelpText');
        if (statusHelpText) {
            if (currentStatus === okStatusId) {
                statusHelpText.textContent = "El defecto está marcado como corregido. Es recomendable subir una imagen de solución.";
                statusHelpText.classList.remove('hidden');
            } else {
                statusHelpText.classList.add('hidden');
            }
        }
        
        // Configurar el evento de cambio en el selector de estado
        statusSelector.addEventListener('change', function() {
            if (parseInt(this.value) === okStatusId) {
                statusHelpText.textContent = "Has marcado el defecto como corregido. Es recomendable subir una imagen de solución.";
                statusHelpText.classList.remove('hidden');
            } else {
                statusHelpText.classList.add('hidden');
            }
        });
    }
    
    // Cerrar el modal de detalles y abrir el de edición
    closeDefectDetailModal();
    document.getElementById('editDefectModal').classList.remove('hidden');
}

// Función para mostrar las imágenes existentes
function displayExistingImages(defect) {
    const defectImagesContainer = document.getElementById('currentDefectImages');
    const locationImagesContainer = document.getElementById('currentLocationImages');
    const solvedImagesContainer = document.getElementById('currentSolvedImages');
    
    // Limpiar contenedores
    defectImagesContainer.innerHTML = '';
    locationImagesContainer.innerHTML = '';
    solvedImagesContainer.innerHTML = '';
    
    // Clasificar imágenes por tipo
    if (defect.images && defect.images.length > 0) {
        defect.images.forEach(image => {
            const imageHtml = `
                <div class="relative group">
                    <img src="${image.image_url}" alt="Imagen" class="w-full h-24 object-cover rounded border border-gray-200">
                    <div class="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-30 transition-all flex items-center justify-center">
                        <button type="button" class="text-white opacity-0 group-hover:opacity-100 transition-opacity" 
                            onclick="showFullImage(event, '${image.image_url}')">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                            </svg>
                        </button>
                    </div>
                </div>
            `;
            
            // Determinar el tipo de imagen basado en el image_type_id o URL
            if (image.image_type_id === 1 || image.image_url.includes('solved')) {
                solvedImagesContainer.innerHTML += imageHtml;
            } else if (image.image_type_id === 2 || image.image_url.includes('location')) {
                locationImagesContainer.innerHTML += imageHtml;
            } else if (image.image_type_id === 3 || image.image_url.includes('defect')) {
                defectImagesContainer.innerHTML += imageHtml;
            }
        });
    }
}

// Función para cerrar el modal de edición
function closeEditModal() {
    document.getElementById('editDefectModal').classList.add('hidden');
}

// Función para manejar el envío del formulario de edición
async function handleDefectFormSubmit(event) {
    event.preventDefault();
    
    const defectId = document.getElementById('editDefectId').value;
    const formData = new FormData(document.getElementById('editDefectForm'));
    
    // Añadir la bandera close_record si está marcada
    const closeRecord = document.getElementById('closeRecord').checked;
    formData.set('close_record', closeRecord);
    
    try {
        // Usar el endpoint correcto para la actualización
        const response = await fetch(`/defect-records/defect-record/${defectId}`, {
            method: 'PATCH',
            body: formData
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Error al actualizar el registro de defecto');
        }
        
        const result = await response.json();
        
        // Verificar si necesitamos recargar los datos completos
        const currentStatus = parseInt(formData.get('status_id'));
        const okStatusId = statuses.find(s => s.status_name === 'Ok')?.status_id;
        
        // Si se marcó como "Ok" y no se subió imagen de solución, mostrar advertencia
        const solvedImages = formData.getAll('solved_images');
        if (currentStatus === okStatusId && solvedImages.length === 0 && !document.getElementById('currentSolvedImages').innerHTML) {
            if (!confirm('Has marcado el defecto como corregido pero no has subido imágenes de solución. ¿Deseas continuar sin agregar una imagen de solución?')) {
                return; // El usuario canceló la operación
            }
        }
        
        // Actualizar datos locales
        await handleJobCodeChange({ target: { value: selectedJobCode } });
        
        // Cerrar el modal de edición
        closeEditModal();
        
        // Mostrar mensaje de éxito
        alert('¡Registro de defecto actualizado con éxito!');
        
    } catch (error) {
        console.error('Error:', error);
        alert(`No se pudo actualizar el registro de defecto: ${error.message}`);
    }
}

// Cerrar modales si se hace clic fuera de ellos
window.addEventListener('click', (event) => {
    const imageModal = document.getElementById('imageModal');
    const defectDetailModal = document.getElementById('defectDetailModal');
    const editDefectModal = document.getElementById('editDefectModal');
    
    if (event.target === imageModal) {
        closeImageModal();
    }
    
    if (event.target === defectDetailModal) {
        closeDefectDetailModal();
    }
    
    if (event.target === editDefectModal) {
        closeEditModal();
    }
});

// Manejar tecla ESC para cerrar modales
document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
        closeImageModal();
        closeDefectDetailModal();
        closeEditModal();
    }
});