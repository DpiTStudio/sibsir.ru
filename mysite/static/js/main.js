// Cheese Boutique Interactivity
document.addEventListener('DOMContentLoaded', () => {
    // 1. Tag filter pill selection
    const tagPills = document.querySelectorAll('.tag-pill');
    const productCards = document.querySelectorAll('.bottom-cards-section .col-md-6, .bottom-cards-section .col-md-12');

    tagPills.forEach(pill => {
        pill.addEventListener('click', () => {
            const isAlreadyActive = pill.classList.contains('active');
            tagPills.forEach(p => p.classList.remove('active'));
            
            if (!isAlreadyActive) {
                pill.classList.add('active');
                const category = pill.getAttribute('data-category');
                console.log('Selected category filter:', category);
            }
        });
    });

    // 2. Cart counter logic
    let cartCount = 0;
    const cartBadge = document.getElementById('cart-counter');

    function updateCart(amount = 1) {
        cartCount += amount;
        if (cartBadge) {
            cartBadge.textContent = cartCount;
            cartBadge.classList.remove('d-none');
            cartBadge.classList.add('animate__animated', 'animate__pulse');
            setTimeout(() => {
                cartBadge.classList.remove('animate__animated', 'animate__pulse');
            }, 600);
        }
    }

    // 3. Pre-select product in modal when clicking "Заказать" on a card
    const orderTriggers = document.querySelectorAll('[data-product]');
    const productSelect = document.getElementById('productSelect');

    orderTriggers.forEach(btn => {
        btn.addEventListener('click', () => {
            const prodName = btn.getAttribute('data-product');
            if (productSelect && prodName) {
                for (let option of productSelect.options) {
                    if (option.value.includes(prodName) || option.text.includes(prodName)) {
                        productSelect.value = option.value;
                        break;
                    }
                }
            }
        });
    });

    // 4. Modal quick order submission via AJAX
    const orderForm = document.getElementById('quickOrderForm');
    const submitBtn = document.getElementById('orderSubmitBtn');

    if (orderForm) {
        orderForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span> Оформление...';
            }

            const formData = new FormData(orderForm);
            const actionUrl = orderForm.getAttribute('action') || '/order/create/';

            try {
                const response = await fetch(actionUrl, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                });

                const data = await response.json();

                if (response.ok && data.success) {
                    const buyModalEl = document.getElementById('buyModal');
                    const orderModal = bootstrap.Modal.getInstance(buyModalEl);
                    if (orderModal) orderModal.hide();

                    updateCart(1);
                    showNotification(data.message || 'Спасибо! Ваш заказ принят. Мы свяжемся с вами в ближайшее время.');
                    orderForm.reset();
                } else {
                    showNotification(data.error || 'Произошла ошибка при отправке заказа. Пожалуйста, попробуйте снова.');
                }
            } catch (err) {
                console.error('Order submission error:', err);
                showNotification('Не удалось отправить заявку. Проверьте подключение к интернету.');
            } finally {
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = '<span>Подтвердить заказ</span> <i class="bi bi-arrow-right ms-2"></i>';
                }
            }
        });
    }

    function showNotification(message) {
        const toastEl = document.getElementById('liveToast');
        if (toastEl) {
            const toastBody = toastEl.querySelector('.toast-body');
            if (toastBody) toastBody.textContent = message;
            const toast = new bootstrap.Toast(toastEl, { delay: 5000 });
            toast.show();
        } else {
            alert(message);
        }
    }
});
