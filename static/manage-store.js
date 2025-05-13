function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function showForm(type) {
    document.getElementById(`${type}-form`).style.display = 'block';
}

function editItem(type, id) {
    fetch(`/manage-store/${storeId}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: `action=edit&item_type=${type}&item_id=${id}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const form = document.getElementById(`${type}Form`);
            form.dataset.itemId = id;  // Store the item ID in the form
            for (const [key, value] of Object.entries(data.item)) {
                const field = form.elements[key];
                if (field) {
                    if (field.type === 'checkbox') {
                        field.checked = value;
                    } else if (field.type === 'date' && value) {
                        field.value = value.split('T')[0];  // Extract date part
                    } else if (key === 'image' && type === 'ad') {
                        // Handle image preview for advertisements
                        const imagePreview = document.getElementById('adImagePreview');
                        if (imagePreview) {
                            imagePreview.src = value;
                            imagePreview.style.display = 'block';
                        }
                    } else {
                        field.value = value || '';
                    }
                }
            }
            showForm(type);
        } else {
            console.error('Error fetching item data:', data);
            alert('Error fetching item data. Please check the console for details.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred. Please check the console for details.');
    });
}

function deleteItem(type, id) {
    if (confirm(`Are you sure you want to delete this ${type}?`)) {
        fetch(`/manage-store/${storeId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: `action=delete&item_type=${type}&item_id=${id}`
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.getElementById(`${type}-${id}`).remove();
            } else {
                alert('Error deleting item');
            }
        });
    }
}

function submitForm(type, form) {
    const formData = new FormData(form);
    const itemId = form.dataset.itemId;
    formData.append('action', itemId ? 'update' : 'create');
    formData.append('item_type', type);
    if (itemId) {
        formData.append('item_id', itemId);
    }

    // Handle image upload for advertisements
    if (type === 'ad' && form.elements['image'].files.length > 0) {
        const file = form.elements['image'].files[0];
        const reader = new FileReader();
        reader.onloadend = function() {
            formData.set('image', reader.result);
            sendFormData(formData);
        }
        reader.readAsDataURL(file);
    } else {
        sendFormData(formData);
    }
}

function sendFormData(formData) {
    fetch(`/manage-store/${storeId}/`, {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.reload();  // Refresh the page to show the new/updated item
        } else {
            console.error('Form errors:', data.errors);
            alert('Error saving item. Please check the console for details.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred. Please check the console for details.');
    });
}

// Add event listeners for form submissions
document.getElementById('offerForm').addEventListener('submit', function(e) {
    e.preventDefault();
    submitForm('offer', this);
});

document.getElementById('adForm').addEventListener('submit', function(e) {
    e.preventDefault();
    submitForm('ad', this);
});

document.getElementById('couponForm').addEventListener('submit', function(e) {
    e.preventDefault();
    submitForm('coupon', this);
});

// Add image preview for advertisements
document.getElementById('adForm').elements['image'].addEventListener('change', function(e) {
    const file = e.target.files[0];
    const reader = new FileReader();
    reader.onloadend = function() {
        const imagePreview = document.getElementById('adImagePreview');
        imagePreview.src = reader.result;
        imagePreview.style.display = 'block';
    }
    if (file) {
        reader.readAsDataURL(file);
    }
});