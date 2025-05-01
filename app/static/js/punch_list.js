// Global variables
let products = [];
let jobCodes = [];
let defectData = [];
let selectedProduct = '';
let selectedJobCode = '';
let currentDefectIndex = -1;
let statuses = [];
let correctionProcesses = [];

// Load products when page starts
document.addEventListener('DOMContentLoaded', () => {
    loadProducts();
    loadStatuses();
    loadCorrectionProcesses();
    
    // Set up event listeners
    document.getElementById('productSelector').addEventListener('change', handleProductChange);
    document.getElementById('jobCodeSelector').addEventListener('change', handleJobCodeChange);
    document.getElementById('editDefectForm').addEventListener('submit', handleDefectFormSubmit);
});

// Function to load products from the API
async function loadProducts() {
    try {
        const response = await fetch('/products');
        if (!response.ok) {
            throw new Error('Error loading products');
        }
        products = await response.json();
        renderProducts(products);
    } catch (error) {
        console.error('Error:', error);
        alert('Could not load products. Please try again later.');
    }
}

// Function to load available statuses
async function loadStatuses() {
    try {
        const response = await fetch('/status');
        if (!response.ok) {
            throw new Error('Error loading statuses');
        }
        statuses = await response.json();
    } catch (error) {
        console.error('Error:', error);
        alert('Could not load statuses. Please try again later.');
    }
}

// Function to load available correction processes
async function loadCorrectionProcesses() {
    try {
        const response = await fetch('/correction-processes');
        if (!response.ok) {
            throw new Error('Error loading correction processes');
        }
        correctionProcesses = await response.json();
        console.log("Correction processes loaded:", correctionProcesses);
    } catch (error) {
        console.error('Error:', error);
        alert('Could not load correction processes. Please try again later.');
    }
}

// Function to render products in the selector
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

// Function to handle product change
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
            throw new Error('Error loading job codes');
        }
        jobCodes = await response.json();
        renderJobCodes(jobCodes);
        
        document.getElementById('jobCodeContainer').classList.remove('hidden');
        document.getElementById('defectsContainer').classList.add('hidden');
        document.getElementById('noDataMessage').classList.add('hidden');
    } catch (error) {
        console.error('Error:', error);
        alert('Could not load job codes. Please try again later.');
    }
}

// Function to render job codes in the selector
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

// Function to handle job code change
async function handleJobCodeChange(event) {
    selectedJobCode = event.target.value;
    
    if (!selectedJobCode || !selectedProduct) {
        document.getElementById('defectsContainer').classList.add('hidden');
        document.getElementById('noDataMessage').classList.add('hidden');
        return;
    }
    
    try {
        // Use the updated endpoint
        const response = await fetch(`/defect-records/complete/${selectedJobCode}/${selectedProduct}`);
        if (!response.ok) {
            throw new Error('Error loading defect data');
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
        alert('Could not load defect data. Please try again later.');
    }
}

// Function to render defects in the table
function renderDefects(defects) {
    const tableBody = document.getElementById('defectsTableBody');
    tableBody.innerHTML = '';
    
    defects.forEach((defect, index) => {
        const row = document.createElement('tr');
        
        // Format dates
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
                        <img src="${image.image_url}" alt="Defect ${imgIndex + 1}" 
                            class="h-16 w-16 object-cover rounded defect-image" 
                            onclick="showFullImage(event, '${image.image_url}')">
                    `).join('')}
                    ${defect.images && defect.images.length > 3 ? `<span class="text-blue-500">+${defect.images.length - 3} more</span>` : ''}
                </div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
                <button 
                    class="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600"
                    onclick="showDefectDetails(${index})">
                    View
                </button>
                <button 
                    class="px-3 py-1 ml-2 bg-yellow-500 text-white rounded hover:bg-yellow-600"
                    onclick="openEditModal(${index})">
                    Edit
                </button>
            </td>
        `;
        
        tableBody.appendChild(row);
    });
}

// Function to show enlarged image
function showFullImage(event, imageSrc) {
    event.stopPropagation(); // Prevent row event activation
    
    document.getElementById('enlargedImage').src = imageSrc;
    document.getElementById('imageModal').classList.remove('hidden');
}

// Function to close image modal
function closeImageModal() {
    document.getElementById('imageModal').classList.add('hidden');
}


// Function to show defect details
function showDefectDetails(index) {
    currentDefectIndex = index;
    const defect = defectData[index];
    const detailContent = document.getElementById('defectDetailContent');
    
    console.log("Showing defect details:", defect);
    console.log("Defect ID:", defect.defect_record_id);
    
    // Get correction process if exists
    let correctionProcessName = '-';
    let correctionProcessId = null;
    
    // Determine correction process ID
    if (defect.correction_process && defect.correction_process.correction_process_id) {
        correctionProcessId = defect.correction_process.correction_process_id;
    } else if (defect.correction_process_id) {
        correctionProcessId = defect.correction_process_id;
    }
    
    // Look first in the loaded list (if already available)
    if (correctionProcessId && correctionProcesses.length > 0) {
        const process = correctionProcesses.find(p => p.correction_process_id === correctionProcessId);
        if (process && process.correction_process_description) {
            correctionProcessName = process.correction_process_description;
        }
    }
    
    // Load correction process description from specific endpoint
    if (correctionProcessId) {
        // Create function to load description
        fetchCorrectionProcessDescription(correctionProcessId)
            .then(description => {
                if (description) {
                    // Update description in DOM
                    const correctionProcessElement = document.querySelector('[data-correction-process-element]');
                    if (correctionProcessElement) {
                        correctionProcessElement.textContent = description;
                    }
                }
            })
            .catch(error => console.error('Error loading correction process description:', error));
    }
    
    // Format dates
    const dateOpened = new Date(defect.date_opened).toLocaleDateString();
    const dateClosed = defect.date_closed ? new Date(defect.date_closed).toLocaleDateString() : '-';
    
    // Organize images by type
    const defectImages = defect.images ? defect.images.filter(img => 
        img.image_type?.type_name === "BEFORE ERROR" || 
        img.image_url.toLowerCase().includes('before') || 
        img.image_url.toLowerCase().includes('defect')
    ) : [];
    
    const locationImages = defect.images ? defect.images.filter(img => 
        img.image_type?.type_name === "LOCATION IMAGE" || 
        img.image_url.toLowerCase().includes('location')
    ) : [];
    
    const solvedImages = defect.images ? defect.images.filter(img => 
        img.image_type?.type_name === "SOLVED IMAGE" || 
        img.image_url.toLowerCase().includes('solved')
    ) : [];
    
    detailContent.innerHTML = `
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="space-y-4">
                <div>
                    <h3 class="text-lg font-medium text-gray-900">General Information</h3>
                    <div class="mt-2 border-t border-gray-200 pt-2">
                        <dl class="divide-y divide-gray-200">
                            <div class="py-2 grid grid-cols-3 gap-4">
                                <dt class="text-sm font-medium text-gray-500">ID:</dt>
                                <dd class="text-sm text-gray-900 col-span-2">${defect.defect_record_id}</dd>
                            </div>
                            <div class="py-2 grid grid-cols-3 gap-4">
                                <dt class="text-sm font-medium text-gray-500">Product:</dt>
                                <dd class="text-sm text-gray-900 col-span-2">${defect.product?.product_name || '-'}</dd>
                            </div>
                            <div class="py-2 grid grid-cols-3 gap-4">
                                <dt class="text-sm font-medium text-gray-500">Defect Description:</dt>
                                <dd class="text-sm text-gray-900 col-span-2">${defect.issue?.issue_description || '-'}</dd>
                            </div>
                            <div class="py-2 grid grid-cols-3 gap-4">
                                <dt class="text-sm font-medium text-gray-500">Process:</dt>
                                <dd class="text-sm text-gray-900 col-span-2">${defect.issue?.process?.process_name || '-'}</dd>
                            </div>
                            <div class="py-2 grid grid-cols-3 gap-4">
                                <dt class="text-sm font-medium text-gray-500">Status:</dt>
                                <dd class="text-sm text-gray-900 col-span-2">
                                    <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full 
                                        ${defect.status?.status_name === 'Ok' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}">
                                        ${defect.status?.status_name || 'N/A'}
                                    </span>
                                </dd>
                            </div>
                            <div class="py-2 grid grid-cols-3 gap-4">
                                <dt class="text-sm font-medium text-gray-500">Correction Process:</dt>
                                <dd class="text-sm text-gray-900 col-span-2" data-correction-process-element>${correctionProcessName}</dd>
                            </div>
                            <div class="py-2 grid grid-cols-3 gap-4">
                                <dt class="text-sm font-medium text-gray-500">Date Opened:</dt>
                                <dd class="text-sm text-gray-900 col-span-2">${dateOpened}</dd>
                            </div>
                            <div class="py-2 grid grid-cols-3 gap-4">
                                <dt class="text-sm font-medium text-gray-500">Date Closed:</dt>
                                <dd class="text-sm text-gray-900 col-span-2">${dateClosed}</dd>
                            </div>
                            <div class="py-2 grid grid-cols-3 gap-4">
                                <dt class="text-sm font-medium text-gray-500">Issue ID:</dt>
                                <dd class="text-sm text-gray-900 col-span-2">${defect.issue_id || '-'}</dd>
                            </div>
                        </dl>
                    </div>
                </div>
                
                <div>
                    <h3 class="text-lg font-medium text-gray-900">Inspector</h3>
                    <div class="mt-2 border-t border-gray-200 pt-2">
                        <dl class="divide-y divide-gray-200">
                            <div class="py-2 grid grid-cols-3 gap-4">
                                <dt class="text-sm font-medium text-gray-500">ID:</dt>
                                <dd class="text-sm text-gray-900 col-span-2">${defect.inspector?.user_id || '-'}</dd>
                            </div>
                            <div class="py-2 grid grid-cols-3 gap-4">
                                <dt class="text-sm font-medium text-gray-500">Employee Number:</dt>
                                <dd class="text-sm text-gray-900 col-span-2">${defect.inspector?.employee_number || '-'}</dd>
                            </div>
                            <div class="py-2 grid grid-cols-3 gap-4">
                                <dt class="text-sm font-medium text-gray-500">Username:</dt>
                                <dd class="text-sm text-gray-900 col-span-2">${defect.inspector?.username || '-'}</dd>
                            </div>
                            <div class="py-2 grid grid-cols-3 gap-4">
                                <dt class="text-sm font-medium text-gray-500">Email:</dt>
                                <dd class="text-sm text-gray-900 col-span-2">${defect.inspector?.email || '-'}</dd>
                            </div>
                            <div class="py-2 grid grid-cols-3 gap-4">
                                <dt class="text-sm font-medium text-gray-500">Full Name:</dt>
                                <dd class="text-sm text-gray-900 col-span-2">
                                    ${defect.inspector?.first_name || '-'} 
                                    ${defect.inspector?.middle_name ? defect.inspector.middle_name : ''} 
                                    ${defect.inspector?.first_surname || ''} 
                                    ${defect.inspector?.second_surname ? defect.inspector.second_surname : ''}
                                </dd>
                            </div>
                            <div class="py-2 grid grid-cols-3 gap-4">
                                <dt class="text-sm font-medium text-gray-500">Role:</dt>
                                <dd class="text-sm text-gray-900 col-span-2">${defect.inspector?.role?.role_name || '-'}</dd>
                            </div>
                        </dl>
                    </div>
                </div>
                
                <div>
                    <h3 class="text-lg font-medium text-gray-900">Error Made By</h3>
                    <div class="mt-2 border-t border-gray-200 pt-2">
                        <dl class="divide-y divide-gray-200">
                            <div class="py-2 grid grid-cols-3 gap-4">
                                <dt class="text-sm font-medium text-gray-500">ID:</dt>
                                <dd class="text-sm text-gray-900 col-span-2">${defect.issue_by_user?.user_id || '-'}</dd>
                            </div>
                            <div class="py-2 grid grid-cols-3 gap-4">
                                <dt class="text-sm font-medium text-gray-500">Employee Number:</dt>
                                <dd class="text-sm text-gray-900 col-span-2">${defect.issue_by_user?.employee_number || '-'}</dd>
                            </div>
                            <div class="py-2 grid grid-cols-3 gap-4">
                                <dt class="text-sm font-medium text-gray-500">Username:</dt>
                                <dd class="text-sm text-gray-900 col-span-2">${defect.issue_by_user?.username || '-'}</dd>
                            </div>
                            <div class="py-2 grid grid-cols-3 gap-4">
                                <dt class="text-sm font-medium text-gray-500">Email:</dt>
                                <dd class="text-sm text-gray-900 col-span-2">${defect.issue_by_user?.email || '-'}</dd>
                            </div>
                            <div class="py-2 grid grid-cols-3 gap-4">
                                <dt class="text-sm font-medium text-gray-500">Full Name:</dt>
                                <dd class="text-sm text-gray-900 col-span-2">
                                    ${defect.issue_by_user?.first_name || '-'} 
                                    ${defect.issue_by_user?.middle_name ? defect.issue_by_user.middle_name : ''} 
                                    ${defect.issue_by_user?.first_surname || ''} 
                                    ${defect.issue_by_user?.second_surname ? defect.issue_by_user.second_surname : ''}
                                </dd>
                            </div>
                            <div class="py-2 grid grid-cols-3 gap-4">
                                <dt class="text-sm font-medium text-gray-500">Role:</dt>
                                <dd class="text-sm text-gray-900 col-span-2">${defect.issue_by_user?.role?.role_name || '-'}</dd>
                            </div>
                        </dl>
                    </div>
                </div>
            </div>
            
            <div>
                <div class="mb-6">
                    <h3 class="text-lg font-medium text-gray-900 mb-3">Defect Images</h3>
                    <div class="grid grid-cols-2 gap-4">
                        ${defectImages.length > 0 ? 
                            defectImages.map((image, imgIndex) => `
                                <div class="border rounded-lg overflow-hidden">
                                    <img src="${image.image_url}" alt="Defect ${imgIndex + 1}" 
                                        class="w-full h-auto object-contain cursor-pointer" 
                                        onclick="showFullImage(event, '${image.image_url}')">
                                    <div class="p-2 bg-gray-50">
                                        <p class="text-sm text-gray-500">Defect Image</p>
                                    </div>
                                </div>
                            `).join('') :
                            '<p class="text-sm text-gray-500 col-span-2">No defect images available</p>'
                        }
                    </div>
                </div>
                
                <div class="mb-6">
                    <h3 class="text-lg font-medium text-gray-900 mb-3">Location Images</h3>
                    <div class="grid grid-cols-2 gap-4">
                        ${locationImages.length > 0 ? 
                            locationImages.map((image, imgIndex) => `
                                <div class="border rounded-lg overflow-hidden">
                                    <img src="${image.image_url}" alt="Location ${imgIndex + 1}" 
                                        class="w-full h-auto object-contain cursor-pointer" 
                                        onclick="showFullImage(event, '${image.image_url}')">
                                    <div class="p-2 bg-gray-50">
                                        <p class="text-sm text-gray-500">Location Image</p>
                                    </div>
                                </div>
                            `).join('') :
                            '<p class="text-sm text-gray-500 col-span-2">No location images available</p>'
                        }
                    </div>
                </div>
                
                <div>
                    <h3 class="text-lg font-medium text-gray-900 mb-3">Solution Images</h3>
                    <div class="grid grid-cols-2 gap-4">
                        ${solvedImages.length > 0 ? 
                            solvedImages.map((image, imgIndex) => `
                                <div class="border rounded-lg overflow-hidden">
                                    <img src="${image.image_url}" alt="Solution ${imgIndex + 1}" 
                                        class="w-full h-auto object-contain cursor-pointer" 
                                        onclick="showFullImage(event, '${image.image_url}')">
                                    <div class="p-2 bg-gray-50">
                                        <p class="text-sm text-gray-500">Solution Image</p>
                                    </div>
                                </div>
                            `).join('') :
                            '<p class="text-sm text-gray-500 col-span-2">No solution images available</p>'
                        }
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.getElementById('defectDetailModal').classList.remove('hidden');
}


// Function to get correction process description
async function fetchCorrectionProcessDescription(correctionProcessId) {
    try {
        const response = await fetch(`http://localhost:8000/correction-processes/${correctionProcessId}`);
        if (!response.ok) {
            throw new Error(`Error getting correction process: ${response.status}`);
        }
        const data = await response.json();
        return data.correction_process_description;
    } catch (error) {
        console.error('Error:', error);
        return null;
    }
}

// Improved function to get image type label based on URL or type
function getImageTypeLabel(image) {
    // First check by image_type if available
    if (image.image_type && image.image_type.type_name) {
        const typeName = image.image_type.type_name.toUpperCase();
        if (typeName === "BEFORE ERROR" || typeName === "DEFECT IMAGE") {
            return 'Defect Image';
        } else if (typeName === "LOCATION IMAGE") {
            return 'Defect Location';
        } else if (typeName === "SOLVED IMAGE") {
            return 'Implemented Solution';
        }
        return image.image_type.type_name; // Return type name as is
    }
    
    // If no image_type, try to deduce from URL
    const imageUrl = image.image_url.toLowerCase();
    if (imageUrl.includes('solved')) {
        return 'Implemented Solution';
    } else if (imageUrl.includes('location')) {
        return 'Defect Location';
    } else if (imageUrl.includes('defect') || imageUrl.includes('before')) {
        return 'Defect Image';
    }
    
    // Default type
    return 'Image';
}

// Function to close details modal
function closeDefectDetailModal() {
    document.getElementById('defectDetailModal').classList.add('hidden');
}

// Function to open edit modal
function openEditModal(index = null) {
    if (index !== null) {
        currentDefectIndex = index;
    }
    
    if (currentDefectIndex === -1) {
        alert('No defect selected for editing.');
        return;
    }
    
    const defect = defectData[currentDefectIndex];
    
    // Fill the form with defect data
    document.getElementById('editDefectId').value = defect.defect_record_id;
    
    // Add hidden fields needed for the model
    if (defect.product && defect.product.product_id) {
        document.getElementById('editProductId').value = defect.product.product_id;
    }
    
    if (defect.job && defect.job.job_id) {
        document.getElementById('editJobId').value = defect.job.job_id;
    }
    
    if (defect.inspector && defect.inspector.user_id) {
        document.getElementById('editInspectorUserId').value = defect.inspector.user_id;
    }
    
    if (defect.issue_by_user && defect.issue_by_user.user_id) {
        document.getElementById('editIssueByUserId').value = defect.issue_by_user.user_id;
    }
    
    if (defect.issue && defect.issue.issue_id) {
        document.getElementById('editIssueId').value = defect.issue.issue_id;
    }
    
    // Populate status selector
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
    
    // Populate correction process selector
    const cpSelector = document.getElementById('editCorrectionProcess');
    cpSelector.innerHTML = '';
    correctionProcesses.forEach(cp => {
        const option = document.createElement('option');
        option.value = cp.correction_process_id;
        option.textContent = cp.correction_process_description; // Use correction_process_description field
        if (defect.correction_process && cp.correction_process_id === defect.correction_process.correction_process_id) {
            option.selected = true;
        }
        cpSelector.appendChild(option);
    });
    
    // Show existing images
    displayExistingImages(defect);
    
    // Check if selected status is "Ok" and show a message
    const currentStatus = defect.status?.status_id;
    const okStatusId = statuses.find(s => s.status_name === 'Ok')?.status_id;
    
    if (okStatusId) {
        const statusHelpText = document.getElementById('statusHelpText');
        if (statusHelpText) {
            if (currentStatus === okStatusId) {
                statusHelpText.textContent = "The defect is marked as corrected. You must upload a solution image.";
                statusHelpText.classList.remove('hidden');
            } else {
                statusHelpText.classList.add('hidden');
            }
        }
        
        // Set up change event on status selector
        statusSelector.addEventListener('change', function() {
            if (parseInt(this.value) === okStatusId) {
                statusHelpText.textContent = "You have marked the defect as corrected. You must upload a solution image.";
                statusHelpText.classList.remove('hidden');
                
                // NEW: Check if there are already solution images
                const hasSolvedImages = document.getElementById('currentSolvedImages').innerHTML.trim() !== '';
                if (!hasSolvedImages) {
                    alert('To mark the defect as OK, you must upload at least one solution image.');
                }
            } else {
                statusHelpText.classList.add('hidden');
            }
        });
        
        // NEW: Add event for solution images input
        const solvedImagesInput = document.getElementById('solvedImages');
        solvedImagesInput.addEventListener('change', function() {
            if (this.files.length > 0) {
                // If a solution image is uploaded, automatically change status to OK
                const okOption = Array.from(statusSelector.options).find(option => parseInt(option.value) === okStatusId);
                if (okOption) {
                    okOption.selected = true;
                    statusHelpText.textContent = "Status has been automatically changed to OK because you uploaded a solution image.";
                    statusHelpText.classList.remove('hidden');
                }
            }
        });
    }
    
    // Close details modal and open edit modal
    closeDefectDetailModal();
    document.getElementById('editDefectModal').classList.remove('hidden');
}

// Function to display existing images
function displayExistingImages(defect) {
    const defectImagesContainer = document.getElementById('currentDefectImages');
    const locationImagesContainer = document.getElementById('currentLocationImages');
    const solvedImagesContainer = document.getElementById('currentSolvedImages');
    
    // Clear containers
    defectImagesContainer.innerHTML = '';
    locationImagesContainer.innerHTML = '';
    solvedImagesContainer.innerHTML = '';
    
    // Classify images by type
    if (defect.images && defect.images.length > 0) {
        defect.images.forEach(image => {
            const imageHtml = `
                <div class="relative group">
                    <img src="${image.image_url}" alt="Image" class="w-full h-24 object-cover rounded border border-gray-200">
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
            
            // Determine image type based on image_type_id or URL
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

// Function to close edit modal
function closeEditModal() {
    document.getElementById('editDefectModal').classList.add('hidden');
}

// Function to handle edit form submission
async function handleDefectFormSubmit(event) {
    event.preventDefault();
    
    // Get defect ID
    const defectId = document.getElementById('editDefectId').value;
    
    // Verify defect ID is valid
    if (!defectId || defectId === 'undefined' || defectId === 'null') {
        alert('Error: Could not identify the defect record to update');
        return;
    }
    
    const formData = new FormData(document.getElementById('editDefectForm'));
    
    // Check for empty fields and remove them to avoid overwriting existing data
    Array.from(formData.entries()).forEach(([key, value]) => {
        if (value === "" || value === null || value === undefined) {
            formData.delete(key);
        }
    });
    
    // MODIFIED: Remove checkbox for closing record
    // Always close record if status is OK
    const currentStatus = parseInt(formData.get('status_id'));
    const okStatusId = statuses.find(s => s.status_name === 'Ok')?.status_id;
    
    if (currentStatus === okStatusId) {
        formData.set('close_record', true);
    } else {
        formData.set('close_record', false);
    }
    
    try {
        // Verify status is "Ok" and has solution images
        const solvedImages = formData.getAll('solved_images');
        const hasSolvedImagesInForm = solvedImages.length > 0 && solvedImages[0].size > 0;
        const hasSolvedImagesExisting = document.getElementById('currentSolvedImages').innerHTML.trim() !== '';
        
        // If marked as "Ok" with no solution images, block submission
        if (currentStatus === okStatusId && !hasSolvedImagesInForm && !hasSolvedImagesExisting) {
            alert('ERROR: To mark a defect as OK, you must add at least one solution image. Please upload a solution image before continuing.');
            return;
        }
        
        console.log(`Sending PATCH to /defect-records/defect-record/${defectId}`);
        
        // Use correct endpoint for update
        const response = await fetch(`/defect-records/defect-record/${defectId}`, {
            method: 'PATCH',
            body: formData
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            let errorMessage;
            try {
                const errorData = JSON.parse(errorText);
                errorMessage = errorData.detail || 'Error updating defect record';
            } catch (e) {
                errorMessage = `Error updating defect record: ${response.status} ${response.statusText}`;
            }
            throw new Error(errorMessage);
        }
        
        const result = await response.json();
        
        // Update local data (reload full list)
        await handleJobCodeChange({ target: { value: selectedJobCode } });
        
        // Close edit modal
        closeEditModal();
        
        // Show success message
        alert('Defect record updated successfully!');
        
    } catch (error) {
        console.error('Error:', error);
        alert(`Could not update defect record: ${error.message}`);
    }
}

// Close modals if clicked outside
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

// Handle ESC key to close modals
document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
        closeImageModal();
        closeDefectDetailModal();
        closeEditModal();
    }
});


async function handleJobCodeChange(event) {
    selectedJobCode = event.target.value;
    
    if (!selectedJobCode || !selectedProduct) {
        document.getElementById('defectsContainer').classList.add('hidden');
        document.getElementById('noDataMessage').classList.add('hidden');
        document.getElementById('processFilterContainer').classList.add('hidden'); // Hide process filter
        return;
    }
    
    try {
        // Use the updated endpoint
        const response = await fetch(`/defect-records/complete/${selectedJobCode}/${selectedProduct}`);
        if (!response.ok) {
            throw new Error('Error loading defect data');
        }
        defectData = await response.json();
        
        if (defectData.length === 0) {
            document.getElementById('defectsContainer').classList.add('hidden');
            document.getElementById('noDataMessage').classList.remove('hidden');
            document.getElementById('processFilterContainer').classList.add('hidden'); // Hide process filter
        } else {
            // Initialize process filter with defect data
            initializeProcessFilter(defectData);
            
            document.getElementById('defectsContainer').classList.remove('hidden');
            document.getElementById('noDataMessage').classList.add('hidden');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Could not load defect data. Please try again later.');
    }
}
