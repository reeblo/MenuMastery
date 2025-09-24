document.addEventListener('DOMContentLoaded', function() {
    // Carousel
    const slides = document.querySelector('.carousel-slides');
    if (slides) {
        const slideItems = document.querySelectorAll('.slide');
        const prevBtn = document.querySelector('.prev');
        const nextBtn = document.querySelector('.next');
        const indicators = document.querySelectorAll('.indicator');
        let currentIndex = 0;
        const totalSlides = slideItems.length;
        let intervalId;

        function goToSlide(index) {
            if (index < 0) {
                index = totalSlides - 1;
            } else if (index >= totalSlides) {
                index = 0;
            }
            
            currentIndex = index;
            slides.style.transform = `translateX(-${currentIndex * 100 / totalSlides}%)`;
            
            indicators.forEach((indicator, i) => {
                indicator.classList.toggle('active', i === currentIndex);
            });
            
            resetAnimations();
        }

        function resetAnimations() {
            const activeSlide = slideItems[currentIndex];
            const h2 = activeSlide.querySelector('h2');
            const p = activeSlide.querySelector('p');
            const btn = activeSlide.querySelector('.btn');
            
            h2.style.animation = 'none';
            p.style.animation = 'none';
            btn.style.animation = 'none';
            
            void h2.offsetWidth;
            void p.offsetWidth;
            void btn.offsetWidth;
            
            h2.style.animation = 'fadeInUp 0.8s ease';
            p.style.animation = 'fadeInUp 0.8s ease 0.2s forwards';
            btn.style.animation = 'fadeInUp 0.8s ease 0.4s forwards';
        }

        prevBtn.addEventListener('click', () => {
            clearInterval(intervalId);
            goToSlide(currentIndex - 1);
            startAutoSlide();
        });

        nextBtn.addEventListener('click', () => {
            clearInterval(intervalId);
            goToSlide(currentIndex + 1);
            startAutoSlide();
        });

        indicators.forEach((indicator, index) => {
            indicator.addEventListener('click', () => {
                clearInterval(intervalId);
                goToSlide(index);
                startAutoSlide();
            });
        });

        function startAutoSlide() {
            intervalId = setInterval(() => {
                goToSlide(currentIndex + 1);
            }, 5000);
        }

        startAutoSlide();

        const carousel = document.querySelector('.carousel-container');
        carousel.addEventListener('mouseenter', () => {
            clearInterval(intervalId);
        });

        carousel.addEventListener('mouseleave', () => {
            startAutoSlide();
        });

        document.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowLeft') {
                clearInterval(intervalId);
                goToSlide(currentIndex - 1);
                startAutoSlide();
            } else if (e.key === 'ArrowRight') {
                clearInterval(intervalId);
                goToSlide(currentIndex + 1);
                startAutoSlide();
            }
        });
    }

    // Checkout buttons
    const checkoutBtn = document.getElementById('checkout-btn');
    if (checkoutBtn) {
        checkoutBtn.addEventListener('click', function() {
            fetch('{{ url_for("carrito") }}', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: 'payment_type=online'
            }).then(response => {
                if (response.redirected) {
                    window.location.href = response.url;
                }
            });
        });
    }

    const cashBtn = document.getElementById('cash-btn');
    if (cashBtn) {
        cashBtn.addEventListener('click', function() {
            fetch('{{ url_for("carrito") }}', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: 'payment_type=cash'
            }).then(response => {
                if (response.redirected) {
                    window.location.href = response.url;
                }
            });
        });
    }

    // Category filters
    document.querySelectorAll('.category-link').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const category = this.getAttribute('data-category');
            
            document.querySelectorAll('.category-link').forEach(item => {
                item.classList.remove('active');
            });
            
            this.classList.add('active');
            
            document.querySelectorAll('.plato-item').forEach(item => {
                if (category === 'all' || item.getAttribute('data-category') === category) {
                    item.style.display = 'block';
                } else {
                    item.style.display = 'none';
                }
            });
        });
    });

    const mobileCategoryFilter = document.getElementById('mobile-category-filter');
    if (mobileCategoryFilter) {
        mobileCategoryFilter.addEventListener('change', function() {
            const category = this.value;
            document.querySelectorAll('.plato-item').forEach(item => {
                if (category === 'all' || item.getAttribute('data-category') === category) {
                    item.style.display = 'block';
                } else {
                    item.style.display = 'none';
                }
            });
        });
    }

    // Real-time reservations update
    if (typeof(EventSource) !== "undefined") {
        const eventSourceReservas = new EventSource('/stream-reservas');
        eventSourceReservas.onmessage = function(e) {
            if (e.data === 'actualizar') {
                location.reload();
            }
        };
    }

    // Assign table modal
    document.querySelectorAll('.btn-asignar-mesa').forEach(btn => {
        btn.addEventListener('click', function() {
            const reservaId = this.dataset.id;
            const form = document.getElementById('formAsignarMesa');
            form.action = `/reserva/${reservaId}/asignar-mesa`;
            
            const modal = new bootstrap.Modal(document.getElementById('modalAsignarMesa'));
            modal.show();
        });
    });

    // Registration form validation
    const registrationForm = document.getElementById('registration-form');
    if (registrationForm) {
        const togglePassword = document.getElementById('toggle-password');
        const passwordField = document.getElementById('password');
        const confirmPasswordField = document.getElementById('confirm_password');
        
        if (togglePassword) {
            togglePassword.addEventListener('click', function() {
                const type = passwordField.getAttribute('type') === 'password' ? 'text' : 'password';
                passwordField.setAttribute('type', type);
                confirmPasswordField.setAttribute('type', type);
                this.classList.toggle('fa-eye-slash');
            });
        }
        
        const emailField = document.getElementById('email');
        const confirmEmailField = document.getElementById('confirm_email');
        
        if (confirmEmailField) {
            confirmEmailField.addEventListener('input', function() {
                if (emailField.value !== confirmEmailField.value) {
                    confirmEmailField.classList.add('is-invalid');
                } else {
                    confirmEmailField.classList.remove('is-invalid');
                }
            });
        }
        
        if (confirmPasswordField) {
            confirmPasswordField.addEventListener('input', function() {
                if (passwordField.value !== confirmPasswordField.value) {
                    confirmPasswordField.classList.add('is-invalid');
                } else {
                    confirmPasswordField.classList.remove('is-invalid');
                }
            });
        }
        
        registrationForm.addEventListener('submit', function(event) {
            let isValid = true;
            
            if (emailField.value !== confirmEmailField.value) {
                confirmEmailField.classList.add('is-invalid');
                isValid = false;
            }
            
            if (passwordField.value !== confirmPasswordField.value) {
                confirmPasswordField.classList.add('is-invalid');
                isValid = false;
            }
            
            if (!document.getElementById('terms').checked) {
                alert('Debes aceptar los términos y condiciones');
                isValid = false;
            }
            
            if (!isValid) {
                event.preventDefault();
                event.stopPropagation();
            }
        });
    }

    // CSRF for all forms
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    document.querySelectorAll('form').forEach(form => {
        if (!form.querySelector('input[name="csrf_token"]')) {
            const csrfInput = document.createElement('input');
            csrfInput.type = 'hidden';
            csrfInput.name = 'csrf_token';
            csrfInput.value = csrfToken;
            form.insertBefore(csrfInput, form.firstChild);
        }
    });

    // Event delegation for cart actions
    document.body.addEventListener('click', async function(e) {
        const target = e.target;

        // Add to cart
        if (target.matches('.add-to-cart') || target.closest('.add-to-cart')) {
            e.preventDefault();
            const button = target.closest('.add-to-cart');
            const form = button.closest('form');
            
            const originalText = button.innerHTML;
            button.disabled = true;
            button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i> Agregando...';
            
            try {
                const formData = new FormData(form);
                const response = await fetch(form.action, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'X-CSRFToken': csrfToken
                    }
                });
                
                const data = await response.json();
                
                if (!response.ok || !data.success) {
                    throw new Error(data.message || 'Error al agregar al carrito');
                }
                
                showToast(data.message, 'success');
                
                const cartCountBadge = document.querySelector('.cart-count');
                if (cartCountBadge) {
                    cartCountBadge.textContent = data.cart_count;
                    cartCountBadge.classList.toggle('d-none', data.cart_count <= 0);
                }
                
            } catch (error) {
                showToast(error.message, 'error');
            } finally {
                button.disabled = false;
                button.innerHTML = originalText;
            }
        }

        // Update quantity in cart
        if (target.matches('.update-quantity-btn')) {
            e.preventDefault();
            const button = target;
            const form = button.closest('form');
            const action = button.dataset.action;
            
            const formData = new FormData(form);
            formData.append('action', action);

            try {
                const response = await fetch(form.action, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-CSRFToken': csrfToken,
                        'Accept': 'application/json'
                    }
                });

                const data = await response.json();
                if (!response.ok || !data.success) throw new Error(data.error || 'Error inesperado');

                const cantidadSpan = form.querySelector('.cantidad-actual');
                if (cantidadSpan) cantidadSpan.textContent = data.newQuantity;

                const fila = form.closest('tr');
                const precioText = fila.querySelector('td:nth-child(2)').textContent.replace('$', '');
                const nuevoSubtotal = parseFloat(precioText) * data.newQuantity;
                fila.querySelector('.subtotal-item').textContent = `$${nuevoSubtotal.toFixed(2)}`;

                document.getElementById('subtotal-general').textContent = `$${data.newTotals.subtotal.toFixed(2)}`;
                document.getElementById('servicio-general').textContent = `$${data.newTotals.servicio.toFixed(2)}`;
                document.getElementById('total-general').textContent = `$${data.newTotals.total.toFixed(2)}`;
            } catch (err) {
                alert(err.message);
                console.error(err);
            }
        }

        // Remove from cart
        if (target.matches('.remove-from-cart-btn')) {
            e.preventDefault();
            const button = target;
            const form = button.closest('form');
            if (confirm('¿Estás seguro de que quieres eliminar este item?')) {
                form.submit();
            }
        }
    });
});

function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast-notification toast-${type}`;
    toast.innerHTML = `
        <div class="toast-body">
            <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'} me-2"></i>
            ${message}
        </div>
    `;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.classList.add('show');
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }, 10);
}
