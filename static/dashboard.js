$(document).ready(function() {
    // Use the global STORE_ID
    const storeId = window.location.pathname.split('/')[1];

    if (!storeId) {
        console.error('Store ID not found. Make sure it\'s properly set in the HTML.');
        return;
    }


    function saveActiveSection(sectionId) {
        localStorage.setItem('activeSection', sectionId);
    }

    // Handle section navigation
    document.querySelectorAll('.sidebar a[data-section]').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const sectionId = this.getAttribute('data-section');

            // Hide all sections
            document.querySelectorAll('main > section').forEach(section => {
                section.classList.remove('active');
            });

            // Hide all submenus
            document.querySelectorAll('.submenu').forEach(submenu => {
                submenu.style.display = 'none';
            });

            // Show the active section
            document.getElementById(sectionId).classList.add('active');

            // If the manage-store section is active, show its submenu
            if (sectionId === 'manage-store') {
                this.nextElementSibling.style.display = 'block';
            }

            saveActiveSection(sectionId);
        });
    });

    // Handle subsection navigation (for Manage Store)
    document.querySelectorAll('.submenu a[data-subsection]').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const subsectionId = this.getAttribute('data-subsection');

            // Hide all subsections within manage-store
            document.querySelectorAll('#manage-store > div.subsection').forEach(subsection => {
                subsection.classList.remove('active');
            });

            // Show the active subsection within manage-store
            document.querySelector(`#manage-store > div#${subsectionId}`).classList.add('active');
        });
    });

    // Load and activate saved section
    function loadActiveSection() {
        const activeSection = localStorage.getItem('activeSection') || 'overview';
        document.querySelector(`.sidebar a[data-section="${activeSection}"]`).click();
    }

    // Chart initialization
    var ctx = document.getElementById('revenueChart').getContext('2d');
    var revenueChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
            datasets: [{
                label: 'Monthly Revenue',
                data: [1200, 1900, 3000, 5000, 2000, 3000],
                borderColor: '#4c241d',
                backgroundColor: 'rgba(235, 182, 5, 0.1)',
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value, index, values) {
                            return '$' + value;
                        }
                    }
                }
            }
        }
    });

    // Edit Menu
    $('#editMenuBtn').click(function() {
        $('#editMenuForm').show();
    });

    $('#editMenuForm form').submit(function(e) {
        e.preventDefault();
        $.ajax({
            url: `/edit/${storeId}/`,
            method: 'POST',
            data: $(this).serialize(),
            success: function(response) {
                alert('Menu updated successfully');
                saveActiveSection('menu');
                location.reload();
            },
            error: function(xhr, status, error) {
                alert('Error updating menu: ' + error);
            }
        });
    });

    // Add Menu Item
    $('#addMenuItem').click(function() {
        $('#editMenuItems').append(`
            <div class="edit-menu-item">
                <input type="text" name="items[]" placeholder="Item Name">
                <input type="text" name="prices[]" placeholder="Price">
            </div>
        `);
    });

    // Fix Menu
    $('#fixMenuBtn').click(function() {
        $.get(`/${storeId}/fix_menu/`, function(data) {
            alert('Menu fixed. Please review the changes.');
            saveActiveSection('menu');
            location.reload();
        });
    });

    // Create Menu
    $('#createMenuBtn').click(function() {
        const url = `/create_menu/`;
        window.open(url, '_blank');
    });

    $('#businessInfoForm').submit(function(e) {
        e.preventDefault();
        
        $.ajax({
            url: window.location.pathname,
            method: 'POST',
            data: $(this).serialize() + '&action=update_business_info',
            success: function(response) {
                if (response.success) {
                    alert('Business information updated successfully.');
                } else {
                    alert('Error updating business information: ' + JSON.stringify(response.errors));
                }
            },
            error: function(xhr, status, error) {
                alert('An error occurred while updating business information.');
            }
        });
    });
    
    // Generate new QR code
    $('#generateQRBtn').click(function() {
        $('.qr-code img').attr('src', `/generate_qr/${storeId}/?` + new Date().getTime());
    });

    // Close modals when clicking outside
    $('.modal').click(function(e) {
        if (e.target === this) {
            $(this).hide();
        }
    });

    // Sidebar toggle functionality
    $('#sidebarToggle').click(function() {
        $('.sidebar').toggleClass('active');
    });

    // Close sidebar when clicking outside on mobile
    $(document).on('click touchstart', function(e) {
        if ($(window).width() <= 768) {
            if (!$(e.target).closest('.sidebar').length && !$(e.target).closest('#sidebarToggle').length) {
                $('.sidebar').removeClass('active');
            }
        }
    });

    // Close sidebar when clicking a link on mobile
    $('.sidebar a').click(function() {
        if ($(window).width() <= 768) {
            $('.sidebar').removeClass('active');
        }
    });

    // Handle window resize
    $(window).resize(function() {
        if ($(window).width() > 768) {
            $('.sidebar').removeClass('active');
        }
    });

    // Orders functionality
    function loadOrders(page = 1) {
        const searchQuery = $('#searchQuery').val();
        const statusFilter = $('#statusFilter').val();
        const orderTypeFilter = $('#orderTypeFilter').val();
        const paymentMethodFilter = $('#paymentMethodFilter').val();
        const sortBy = $('#sortBy').val();
    
        $.ajax({
            url: `/${storeId}/my-orders/`,
            data: {
                page: page,
                search: searchQuery,
                status: statusFilter,
                order_type: orderTypeFilter,
                payment_method: paymentMethodFilter,
                sort_by: sortBy
            },
            success: function(response) {
                displayOrders(response.orders);
                displayPagination(response);
            },
            error: function(xhr, status, error) {
                console.error("Error fetching orders:", error);
                $('#ordersList').html('<p>Error loading orders. Please try again.</p>');
            }
        });
    }
    
    function displayOrders(orders) {
        const ordersList = $('#ordersList');
        ordersList.empty();
    
        if (!orders || orders.length === 0) {
            ordersList.html('<p>No orders found.</p>');
            return;
        }
    
        orders.forEach(order => {
            const orderHtml = `
                <div class="order-item" data-order-id="${order.id}">
                    <div class="order-header">
                        <h3>Order #${order.store_order_id || 'N/A'}</h3>
                        <span class="status ${(order.status || '').toLowerCase()}">${order.status || 'Unknown'}</span>
                    </div>
                    <div class="order-details">
                        <p><strong>Customer:</strong> ${order.customer_name || 'N/A'} (${order.customer_phone || 'N/A'})</p>
                        <p><strong>Total:</strong> $${order.total_price || '0.00'}</p>
                        <p><strong>Type:</strong> ${order.order_type || 'N/A'}</p>
                        <p><strong>Payment:</strong> ${order.payment_method || 'N/A'}</p>
                        <p><strong>Date:</strong> ${order.created_at ? new Date(order.created_at).toLocaleString() : 'N/A'}</p>
                    </div>
                    <div class="order-items">
                        <h4>Items:</h4>
                        <ul>
                            ${(order.items || []).map(item => `
                                <li>${item.item_name || 'Unknown Item'} x${item.quantity || 0} - $${item.price || '0.00'}</li>
                            `).join('')}
                        </ul>
                    </div>
                    ${order.status !== 'COMPLETED' ? `
                        <button class="confirm-payment-btn" data-order-id="${order.id}">Confirm Payment</button>
                    ` : ''}
                </div>
            `;
            ordersList.append(orderHtml);
        });
    
        // Add event listener for confirmation buttons
        $('.confirm-payment-btn').click(function() {
            const orderId = $(this).data('order-id');
            confirmPayment(orderId);
        });
    }

    function confirmPayment(orderId) {
        $.ajax({
            url: `/${storeId}/order/${orderId}/confirm-payment/`,
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken()
            },
            success: function(response) {
                if (response.success) {
                    alert('Payment confirmed successfully.');
                    // Update the order status in the UI
                    const orderElement = $(`.order-item[data-order-id="${orderId}"]`);
                    orderElement.find('.status').text('COMPLETED').removeClass().addClass('status completed');
                    orderElement.find('.confirm-payment-btn').remove();
                } else {
                    alert('Failed to confirm payment: ' + response.error);
                }
            },
            error: function(xhr, status, error) {
                alert('An error occurred while confirming payment: ' + error);
            }
        });
    }
    
    function getCsrfToken() {
        return $('[name=csrfmiddlewaretoken]').val();
    }

    
    function displayPagination(response) {
        const pagination = $('#pagination');
        pagination.empty();
    
        if (response.has_previous) {
            pagination.append('<button class="prev-page">Previous</button>');
        }
    
        pagination.append(`<span>Page ${response.current_page} of ${response.num_pages}</span>`);
    
        if (response.has_next) {
            pagination.append('<button class="next-page">Next</button>');
        }
    }
    
    // Load orders when the page loads
    loadOrders();
    
    // Handle filter, sort, and search changes
    $('#searchQuery, #statusFilter, #orderTypeFilter, #paymentMethodFilter, #sortBy').on('change keyup', function() {
        loadOrders();
    });
    
    // Handle pagination
    $('#pagination').on('click', '.prev-page', function() {
        loadOrders(parseInt($('#pagination span').text().split(' ')[1]) - 1);
    });
    
    $('#pagination').on('click', '.next-page', function() {
        loadOrders(parseInt($('#pagination span').text().split(' ')[1]) + 1);
    });    

    loadActiveSection();
});