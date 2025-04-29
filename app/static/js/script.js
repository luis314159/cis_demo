// Global variables
let products = [];
let jobCodes = [];
let defectData = [];
let selectedProduct = '';
let selectedJobCode = '';
let currentDefectIndex = -1;
let statuses = [];
let correctionProcesses = [];

// Upload form elements
const uploadForm = document.getElementById("uploadForm");
const fileInput = document.getElementById("fileInput");
const fileName = document.getElementById("fileName");
const notification = document.getElementById("notification");
const spinner = document.getElementById("spinner");
const productSelect = document.getElementById("productSelect");

// Initialize page based on which elements are present
document.addEventListener("DOMContentLoaded", async () => {
    console.log("DOM Content Loaded");
    
    // Check if we're on the upload page
    if (uploadForm) {
        console.log("Upload form detected - initializing upload page");
        initUploadPage();
    } 
    // Check if we're on the defect management page
    else if (document.getElementById('productSelector')) {
        console.log("Product selector detected - initializing defect management page");
        initDefectManagementPage();
    }
});

// Initialize the upload page
function initUploadPage() {
    console.log("Initializing upload page");
    loadProductsForUpload();
    
    // Show the name of the selected file
    if (fileInput) {
        fileInput.addEventListener("change", () => {
            if (fileInput.files.length > 0) {
                fileName.textContent = `Selected file: ${fileInput.files[0].name}`;
                fileName.classList.remove("hidden");
            } else {
                fileName.textContent = "No file selected";
                fileName.classList.add("hidden");
            }
        });
    }
    
    // Handle form submission
    if (uploadForm) {
        uploadForm.addEventListener("submit", handleFormSubmit);
    }
}

// Initialize the defect management page
function initDefectManagementPage() {
    console.log("Initializing defect management page");
    loadProducts();
    loadStatuses();
    loadCorrectionProcesses();
    
    // Set up event listeners
    const productSelector = document.getElementById('productSelector');
    if (productSelector) {
        productSelector.addEventListener('change', handleProductChange);
    }
    
    const jobCodeSelector = document.getElementById('jobCodeSelector');
    if (jobCodeSelector) {
        jobCodeSelector.addEventListener('change', handleJobCodeChange);
    }
    
    const editDefectForm = document.getElementById('editDefectForm');
    if (editDefectForm) {
        editDefectForm.addEventListener('submit', handleDefectFormSubmit);
    }
}

// Load products for the upload page
async function loadProductsForUpload() {
    try {
        showSpinner();
        console.log("Fetching products from /products/ endpoint...");
        
        // Use the correct endpoint to get products
        const response = await fetch("/products/");
        console.log("Response status:", response.status);
        
        if (!response.ok) {
            console.error("Response not OK:", response.status, response.statusText);
            showNotification("Error loading products.", "error");
            return;
        }
        
        // Get response as text first for debugging
        const responseText = await response.text();
        console.log("Raw response:", responseText);
        
        // Only try to parse if we have content
        if (!responseText.trim()) {
            console.error("Empty response received");
            showNotification("Received empty response from server.", "error");
            return;
        }
        
        // Try to parse JSON
        let products;
        try {
            products = JSON.parse(responseText);
        } catch (parseError) {
            console.error("JSON parse error:", parseError);
            showNotification("Error parsing product data.", "error");
            return;
        }
        
        console.log("Parsed products:", products);
        
        // Check if products is an array
        if (!Array.isArray(products)) {
            console.error("Products is not an array:", products);
            showNotification("Unexpected product data format.", "error");
            return;
        }

        // Clear previous options
        productSelect.innerHTML = '<option value="" selected disabled>-- Select a product --</option>';

        // Add products to the selector
        products.forEach(product => {
            try {
                const option = document.createElement("option");
                option.value = product.product_id;
                option.textContent = product.product_name;
                productSelect.appendChild(option);
                console.log(`Added product: ${product.product_name}`);
            } catch (err) {
                console.error("Error adding product option:", err, product);
            }
        });
        
        console.log("Products loaded successfully");
    } catch (error) {
        console.error("Error in product loading process:", error);
        showNotification("Could not load products. Please try again later.", "error");
    } finally {
        hideSpinner();
    }
}

// Handle upload form submission
async function handleFormSubmit(e) {
    e.preventDefault();

    // Validate product selection
    const selectedProduct = productSelect.value;
    const selectedProductText = productSelect.options[productSelect.selectedIndex]?.text || "";

    if (!selectedProduct) {
        showNotification("Please select a product.", "error");
        return;
    }

    // Validate file selection
    if (!fileInput.files.length) {
        showNotification("Please select a file.", "error");
        return;
    }

    showSpinner();

    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append("file", file);

    try {
        console.log("Sending data: ", {
            file: fileInput.files[0].name,
            product_name: selectedProductText
        });

        // Send product_name as query parameter
        const response = await fetch(`/object/validate-and-insert?product_name=${encodeURIComponent(selectedProductText)}`, {
            method: "POST",
            body: formData,
        });

        if (!response.ok) {
            // Try to get error details
            try {
                const errorData = await response.json();
                const errorMessage = typeof errorData === 'object' ? 
                    (errorData.detail && typeof errorData.detail === 'object' ? 
                        errorData.detail.error || JSON.stringify(errorData.detail) : 
                        errorData.detail || JSON.stringify(errorData)) : 
                    errorData;
                showNotification(`Error: ${errorMessage}`, "error");
                console.error("Detailed error:", errorData);
            } catch (jsonError) {
                showNotification(`Error ${response.status}: ${response.statusText}`, "error");
                console.error("Response status:", response.status, response.statusText);
            }
            return;
        }

        const result = await response.json();
        showNotification(result.message || "File processed successfully!", "success");

        // Reset the form after successful submission
        uploadForm.reset();
        fileName.textContent = "No file selected";
        fileName.classList.add("hidden");

    } catch (error) {
        showNotification("An error occurred while uploading the file.", "error");
        console.error("Upload error:", error);
    } finally {
        hideSpinner();
    }
}

// Load products for the defect management page
async function loadProducts() {
    try {
        console.log("Fetching products from /products/ endpoint...");
        const response = await fetch('/products/');
        
        console.log("Response status:", response.status);
        
        if (!response.ok) {
            console.error("Response not OK:", response.status, response.statusText);
            throw new Error('Error loading products');
        }
        
        // Get response as text first for debugging
        const responseText = await response.text();
        console.log("Raw response:", responseText);
        
        // Try to parse JSON
        let productsData;
        try {
            productsData = JSON.parse(responseText);
        } catch (parseError) {
            console.error("JSON parse error:", parseError);
            throw new Error('Error parsing product data');
        }
        
        console.log("Parsed products:", productsData);
        
        // Check if products is an array
        if (!Array.isArray(productsData)) {
            console.error("Products is not an array:", productsData);
            throw new Error('Unexpected product data format');
        }
        
        products = productsData;
        renderProducts(products);
    } catch (error) {
        console.error('Error loading products:', error);
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
        
        // Get response as text first for debugging
        const responseText = await response.text();
        console.log("Raw status response:", responseText);
        
        // Try to parse JSON
        try {
            statuses = JSON.parse(responseText);
        } catch (parseError) {
            console.error("Status JSON parse error:", parseError);
            throw new Error('Error parsing status data');
        }
    } catch (error) {
        console.error('Error loading statuses:', error);
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
        
        // Get response as text first for debugging
        const responseText = await response.text();
        console.log("Raw correction processes response:", responseText);
        
        // Try to parse JSON
        try {
            correctionProcesses = JSON.parse(responseText);
        } catch (parseError) {
            console.error("Correction processes JSON parse error:", parseError);
            throw new Error('Error parsing correction process data');
        }
    } catch (error) {
        console.error('Error loading correction processes:', error);
        alert('Could not load correction processes. Please try again later.');
    }
}

// Function to render products in the selector
function renderProducts(products) {
    const productSelector = document.getElementById('productSelector');
    if (!productSelector) {
        console.error("Product selector element not found!");
        return;
    }
    
    // Save the default option if it exists
    const defaultOption = productSelector.querySelector('option');
    
    productSelector.innerHTML = '';
    if (defaultOption) {
        productSelector.appendChild(defaultOption);
    } else {
        const newDefaultOption = document.createElement('option');
        newDefaultOption.value = "";
        newDefaultOption.textContent = "-- Select a product --";
        newDefaultOption.disabled = true;
        newDefaultOption.selected = true;
        productSelector.appendChild(newDefaultOption);
    }
    
    products.forEach(product => {
        try {
            const option = document.createElement('option');
            option.value = product.product_name;
            option.textContent = product.product_name;
            productSelector.appendChild(option);
            console.log(`Added product option: ${product.product_name}`);
        } catch (err) {
            console.error("Error creating product option:", err, product);
        }
    });
    
    console.log("Products rendered successfully");
}

// Function to handle product change
async function handleProductChange(event) {
    selectedProduct = event.target.value;
    console.log("Selected product:", selectedProduct);
    
    if (!selectedProduct) {
        document.getElementById('jobCodeContainer').classList.add('hidden');
        document.getElementById('defectsContainer').classList.add('hidden');
        document.getElementById('noDataMessage').classList.add('hidden');
        return;
    }
    
    try {
        console.log(`Fetching job codes for product: ${selectedProduct}`);
        const response = await fetch(`/jobs/list-by-product/${selectedProduct}`);
        
        if (!response.ok) {
            console.error("Error response from job codes endpoint:", response.status, response.statusText);
            throw new Error('Error loading job codes');
        }
        
        // Get response as text first for debugging
        const responseText = await response.text();
        console.log("Raw job codes response:", responseText);
        
        // Try to parse JSON
        try {
            jobCodes = JSON.parse(responseText);
        } catch (parseError) {
            console.error("Job codes JSON parse error:", parseError);
            throw new Error('Error parsing job codes data');
        }
        
        console.log("Parsed job codes:", jobCodes);
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
    if (!jobCodeSelector) {
        console.error("Job code selector element not found!");
        return;
    }
    
    // Save the default option if it exists
    const defaultOption = jobCodeSelector.querySelector('option');
    
    jobCodeSelector.innerHTML = '';
    if (defaultOption) {
        jobCodeSelector.appendChild(defaultOption);
    } else {
        const newDefaultOption = document.createElement('option');
        newDefaultOption.value = "";
        newDefaultOption.textContent = "-- Select a job code --";
        newDefaultOption.disabled = true;
        newDefaultOption.selected = true;
        jobCodeSelector.appendChild(newDefaultOption);
    }
    
    jobCodes.forEach(job => {
        try {
            const option = document.createElement('option');
            option.value = job.job_code;
            option.textContent = job.job_code;
            jobCodeSelector.appendChild(option);
            console.log(`Added job code option: ${job.job_code}`);
        } catch (err) {
            console.error("Error creating job code option:", err, job);
        }
    });
    
    console.log("Job codes rendered successfully");
}

// Function to handle job code change
async function handleJobCodeChange(event) {
    selectedJobCode = event.target.value;
    console.log("Selected job code:", selectedJobCode);
    
    if (!selectedJobCode || !selectedProduct) {
        document.getElementById('defectsContainer').classList.add('hidden');
        document.getElementById('noDataMessage').classList.add('hidden');
        return;
    }
    
    try {
        // Use the updated endpoint
        console.log(`Fetching defect data for job code: ${selectedJobCode}, product: ${selectedProduct}`);
        const response = await fetch(`/defect-records/complete/${selectedJobCode}/${selectedProduct}`);
        
        if (!response.ok) {
            console.error("Error response from defect records endpoint:", response.status, response.statusText);
            throw new Error('Error loading defect data');
        }
        
        // Get response as text first for debugging
        const responseText = await response.text();
        console.log("Raw defect data response:", responseText);
        
        // Try to parse JSON
        try {
            defectData = JSON.parse(responseText);
        } catch (parseError) {
            console.error("Defect data JSON parse error:", parseError);
            throw new Error('Error parsing defect data');
        }
        
        console.log("Parsed defect data:", defectData);
        
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
    if (!tableBody) {
        console.error("Defects table body element not found!");
        return;
    }
    
    tableBody.innerHTML = '';
    
    defects.forEach((defect, index) => {
        try {
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
        } catch (err) {
            console.error("Error creating defect row:", err, defect);
        }
    });
    
    console.log("Defects rendered successfully");
}

// Function to show enlarged image
function showFullImage(event, imageSrc) {
    event.stopPropagation(); // Prevent row event from activating
    
    const enlargedImageElement = document.getElementById('enlargedImage');
    if (!enlargedImageElement) {
        console.error("Enlarged image element not found!");
        return;
    }
    
    enlargedImageElement.src = imageSrc;
    
    const imageModalElement = document.getElementById('imageModal');
    if (!imageModalElement) {
        console.error("Image modal element not found!");
        return;
    }
    
    imageModalElement.classList.remove('hidden');
}

// Function to close the image modal
function closeImageModal() {
    const imageModalElement = document.getElementById('imageModal');
    if (!imageModalElement) {
        console.error("Image modal element not found!");
        return;
    }
    
    imageModalElement.classList.add('hidden');
}

// Function to show defect details
function showDefectDetails(index) {
    currentDefectIndex = index;
    const defect = defectData[index];
    const detailContent = document.getElementById('defectDetailContent');
    if (!detailContent) {
        console.error("Defect detail content element not found!");
        return;
    }
    
    // Format dates
    const dateOpened = new Date(defect.date_opened).toLocaleDateString();
    const dateClosed = defect.date_closed ? new Date(defect.date_closed).toLocaleDateString() : '-';
    
    detailContent.innerHTML = `
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="space-y-4">
                <div>
                    <h3 class="text-lg font-medium text-gray-900">General Information</h3>
                    <div class="mt-2 border-t border-gray-200 pt-2">
                        <dl class="divide-y divide-gray-200">
                            <div class="py-2 grid grid-cols-3 gap-4">
                                <dt class="text-sm font-medium text-gray-500">Product:</dt>
                                <dd class="text-sm text-gray-900 col-span-2">${defect.product?.product_name || '-'}</dd>
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
                                <dt class="text-sm font-medium text-gray-500">Open Date:</dt>
                                <dd class="text-sm text-gray-900 col-span-2">${dateOpened}</dd>
                            </div>
                            <div class="py-2 grid grid-cols-3 gap-4">
                                <dt class="text-sm font-medium text-gray-500">Close Date:</dt>
                                <dd class="text-sm text-gray-900 col-span-2">${dateClosed}</dd>
                            </div>
                            ${defect.description ? `
                            <div class="py-2 grid grid-cols-3 gap-4">
                                <dt class="text-sm font-medium text-gray-500">Description:</dt>
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
                                <dt class="text-sm font-medium text-gray-500">Employee Number:</dt>
                                <dd class="text-sm text-gray-900 col-span-2">${defect.inspector?.employee_number || '-'}</dd>
                            </div>
                            <div class="py-2 grid grid-cols-3 gap-4">
                                <dt class="text-sm font-medium text-gray-500">Full Name:</dt>
                                <dd class="text-sm text-gray-900 col-span-2">${defect.inspector?.first_name || '-'} ${defect.inspector?.first_surname || ''}</dd>
                            </div>
                            <div class="py-2 grid grid-cols-3 gap-4">
                                <dt class="text-sm font-medium text-gray-500">Role:</dt>
                                <dd class="text-sm text-gray-900 col-span-2">${defect.inspector?.role?.role_name || '-'}</dd>
                            </div>
                        </dl>
                    </div>
                </div>
                
                <div>
                    <h3 class="text-lg font-medium text-gray-900">User Error</h3>
                    <div class="mt-2 border-t border-gray-200 pt-2">
                        <dl class="divide-y divide-gray-200">
                            <div class="py-2 grid grid-cols-3 gap-4">
                                <dt class="text-sm font-medium text-gray-500">Employee Number:</dt>
                                <dd class="text-sm text-gray-900 col-span-2">${defect.issue_by_user?.employee_number || '-'}</dd>
                            </div>
                            <div class="py-2 grid grid-cols-3 gap-4">
                                <dt class="text-sm font-medium text-gray-500">Full Name:</dt>
                                <dd class="text-sm text-gray-900 col-span-2">${defect.issue_by_user?.first_name || '-'} ${defect.issue_by_user?.first_surname || ''}</dd>
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
                <h3 class="text-lg font-medium text-gray-900 mb-3">Images</h3>
                <div class="grid grid-cols-1 gap-4">
                    ${defect.images && defect.images.map((image, imgIndex) => `
                        <div class="border rounded-lg overflow-hidden">
                            <img src="${image.image_url}" alt="Defect ${imgIndex + 1}" 
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
    
    const defectDetailModal = document.getElementById('defectDetailModal');
    if (defectDetailModal) {
        defectDetailModal.classList.remove('hidden');
    } else {
        console.error("Defect detail modal element not found!");
    }
}

// Function to get image type based on URL
function getImageTypeLabel(image) {
    // First check by image_type_id if available
    if (image.image_type_id === 1) {
        return 'Implemented Solution';
    } else if (image.image_type_id === 2) {
        return 'Defect Location';
    } else if (image.image_type_id === 3) {
        return 'Defect Image';
    }

    // If no image_type_id, try to determine by URL
    const imageUrl = image.image_url.toLowerCase();
    if (imageUrl.includes('solved')) {
        return 'Implemented Solution';
    } else if (imageUrl.includes('location')) {
        return 'Defect Location';
    } else if (imageUrl.includes('defect')) {
        return 'Defect Image';
    }
    return 'Image';
}

// Function to close the details modal
function closeDefectDetailModal() {
    const defectDetailModal = document.getElementById('defectDetailModal');
    if (defectDetailModal) {
        defectDetailModal.classList.add('hidden');
    } else {
        console.error("Defect detail modal element not found!");
    }
}

// Function to open the edit modal
function openEditModal(index = null) {
    if (index !== null) {
        currentDefectIndex = index;
    }
    
    if (currentDefectIndex === -1) {
        alert('No defect has been selected for editing.');
        return;
    }
    
    const defect = defectData[currentDefectIndex];
    
    // Fill the form with defect data
    const editDefectId = document.getElementById('editDefectId');
    if (editDefectId) {
        editDefectId.value = defect.defect_record_id;
    }
    
    const editDescription = document.getElementById('editDescription');
    if (editDescription) {
        editDescription.value = defect.description || '';
    }
    
    // Populate the status selector
    const statusSelector = document.getElementById('editStatus');
    if (statusSelector) {
        statusSelector.innerHTML = '';
        statuses.forEach(status => {
            try {
                const option = document.createElement('option');
                option.value = status.status_id;
                option.textContent = status.status_name;
                if (defect.status && status.status_id === defect.status.status_id) {
                    option.selected = true;
                }
                statusSelector.appendChild(option);
            } catch (err) {
                console.error("Error creating status option:", err, status);
            }
        });
    }
    
    // Populate the correction process selector
    const cpSelector = document.getElementById('editCorrectionProcess');
    if (cpSelector) {
        cpSelector.innerHTML = '';
        correctionProcesses.forEach(cp => {
            try {
                const option = document.createElement('option');
                option.value = cp.correction_process_id;
                option.textContent = cp.process_name;
                if (defect.correction_process && cp.correction_process_id === defect.correction_process.correction_process_id) {
                    option.selected = true;
                }
                cpSelector.appendChild(option);
            } catch (err) {
                console.error("Error creating correction process option:", err, cp);
            }
        });
    }
    
    // Show existing images
    displayExistingImages(defect);
    
    // If the defect is already closed, check the box
    const closeRecord = document.getElementById('closeRecord');
    if (closeRecord) {
        closeRecord.checked = !!defect.date_closed;
    }
    
    // Check if the selected status is "Ok" and show a message
    const currentStatus = defect.status?.status_id;
    const okStatusId = statuses.find(s => s.status_name === 'Ok')?.status_id;
    
    if (okStatusId && statusSelector) {
        const statusHelpText = document.getElementById('statusHelpText');
        if (statusHelpText) {
            if (currentStatus === okStatusId) {
                statusHelpText.textContent = "The defect is marked as corrected. It is recommended to upload a solution image.";
                statusHelpText.classList.remove('hidden');
            } else {
                statusHelpText.classList.add('hidden');
            }
            
            // Set up change event on the status selector
            statusSelector.addEventListener('change', function() {
                if (parseInt(this.value) === okStatusId) {
                    statusHelpText.textContent = "You have marked the defect as corrected. It is recommended to upload a solution image.";
                    statusHelpText.classList.remove('hidden');
                } else {
                    statusHelpText.classList.add('hidden');
                }
            });
        }
    }
    
    // Close the details modal and open the edit modal
    closeDefectDetailModal();
    
    const editDefectModal = document.getElementById('editDefectModal');
    if (editDefectModal) {
        editDefectModal.classList.remove('hidden');
    } else {
        console.error("Edit defect modal element not found!");
    }
}

// Function to display existing images
function displayExistingImages(defect) {
    const defectImagesContainer = document.getElementById('currentDefectImages');
    const locationImagesContainer = document.getElementById('currentLocationImages');
    const solvedImagesContainer = document.getElementById('currentSolvedImages');
    
    // Make sure all containers exist
    if (!defectImagesContainer || !locationImagesContainer || !solvedImagesContainer) {
        console.error("One or more image containers not found!");
        return;
    }
    
    // Clear containers
    defectImagesContainer.innerHTML = '';
    locationImagesContainer.innerHTML = '';
    solvedImagesContainer.innerHTML = '';
    
    // Classify images by type
    if (defect.images && defect.images.length > 0) {
        defect.images.forEach(image => {
            try {
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
            } catch (err) {
                console.error("Error displaying image:", err, image);
            }
        });
    }
}

// Function to close the edit modal
function closeEditModal() {
    const editDefectModal = document.getElementById('editDefectModal');
    if (editDefectModal) {
        editDefectModal.classList.add('hidden');
    } else {
        console.error("Edit defect modal element not found!");
    }
}

// Function to handle edit form submission
async function handleDefectFormSubmit(event) {
    event.preventDefault();
    
    const editDefectId = document.getElementById('editDefectId');
    if (!editDefectId) {
        console.error("Edit defect ID element not found!");
        return;
    }
    
    const defectId = editDefectId.value;
    const editDefectForm = document.getElementById('editDefectForm');
    if (!editDefectForm) {
        console.error("Edit defect form element not found!");
        return;
    }
    
    const formData = new FormData(editDefectForm);
    
    // Add close_record flag if checked
    const closeRecord = document.getElementById('closeRecord');
    if (closeRecord) {
        formData.set('close_record', closeRecord.checked);
    }
    
    try {
        console.log(`Updating defect record ID: ${defectId}`);
        // Use the correct endpoint for updating
        const response = await fetch(`/defect-records/defect-record/${defectId}`, {
            method: 'PATCH',
            body: formData
        });
        
        if (!response.ok) {
            // Get response as text first for debugging
            const responseText = await response.text();
            console.error("Error updating defect record - raw response:", responseText);
            
            // Try to parse JSON error
            try {
                const errorData = JSON.parse(responseText);
                throw new Error(errorData.detail || 'Error updating defect record');
            } catch (parseError) {
                throw new Error(`Error updating defect record: ${response.status} ${response.statusText}`);
            }
        }
        
        // Get response as text first for debugging
        const responseText = await response.text();
        console.log("Update response:", responseText);
        
        // Parse result JSON
        let result;
        try {
            result = JSON.parse(responseText);
        } catch (parseError) {
            console.error("Result JSON parse error:", parseError);
            throw new Error('Error parsing update result');
        }
        
        // Check if we need to reload complete data
        const currentStatus = parseInt(formData.get('status_id'));
        const okStatusId = statuses.find(s => s.status_name === 'Ok')?.status_id;
        
        // If marked as "Ok" but no solution image uploaded, show warning
        const solvedImages = formData.getAll('solved_images');
        const currentSolvedImages = document.getElementById('currentSolvedImages');
        if (currentStatus === okStatusId && solvedImages.length === 0 && (!currentSolvedImages || !currentSolvedImages.innerHTML)) {
            if (!confirm('You have marked the defect as corrected but have not uploaded solution images. Do you want to continue without adding a solution image?')) {
                return; // User canceled the operation
            }
        }
        
        // Update local data
        await handleJobCodeChange({ target: { value: selectedJobCode } });
        
        // Close the edit modal
        closeEditModal();
        
        // Show success message
        alert('Defect record updated successfully!');
        
    } catch (error) {
        console.error('Error:', error);
        alert(`Could not update defect record: ${error.message}`);
    }
}

// Show notification
function showNotification(message, type) {
    const notification = document.getElementById("notification");
    if (!notification) {
        console.error("Notification element not found!");
        alert(message);
        return;
    }
    
    notification.textContent = message;
    notification.className = `notification ${type}`;
    notification.classList.remove("hidden");

    setTimeout(() => {
        notification.classList.add("hidden");
    }, 5000);
}

// Show spinner
function showSpinner() {
    const spinner = document.getElementById("spinner");
    if (spinner) {
        spinner.classList.remove("hidden");
    }
}

// Hide spinner
function hideSpinner() {
    const spinner = document.getElementById("spinner");
    if (spinner) {
        spinner.classList.add("hidden");
    }
}

// Close modals when clicking outside them
window.addEventListener('click', (event) => {
    const imageModal = document.getElementById('imageModal');
    const defectDetailModal = document.getElementById('defectDetailModal');
    const editDefectModal = document.getElementById('editDefectModal');
    
    if (imageModal && event.target === imageModal) {
        closeImageModal();
    }
    
    if (defectDetailModal && event.target === defectDetailModal) {
        closeDefectDetailModal();
    }
    
    if (editDefectModal && event.target === editDefectModal) {
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