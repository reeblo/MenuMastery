//carrusel
document.addEventListener('DOMContentLoaded', function() {
    const slides = document.querySelector('.carousel-slides');
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
        
        // Actualizar indicadores
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

    // Autoplay
    function startAutoSlide() {
        intervalId = setInterval(() => {
            goToSlide(currentIndex + 1);
        }, 5000);
    }

    // Iniciar autoplay
    startAutoSlide();

    // Pausar autoplay al hacer hover
    const carousel = document.querySelector('.carousel-container');
    carousel.addEventListener('mouseenter', () => {
        clearInterval(intervalId);
    });

    carousel.addEventListener('mouseleave', () => {
        startAutoSlide();
    });

    // Manejo de teclado
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
});


//carro de compras
document.getElementById('checkout-btn').addEventListener('click', function() {
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

document.getElementById('cash-btn').addEventListener('click', function() {
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


// menu
// Función para mostrar notificación
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

// Filtrado por categorías (funcionalidad existente)
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

// Filtro móvil
document.getElementById('mobile-category-filter').addEventListener('change', function() {
    const category = this.value;
    document.querySelectorAll('.plato-item').forEach(item => {
        if (category === 'all' || item.getAttribute('data-category') === category) {
            item.style.display = 'block';
        } else {
            item.style.display = 'none';
        }
    });
});

// Manejo del formulario para agregar al carrito
document.querySelectorAll('form[action*="agregar-al-carrito"]').forEach(form => {
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const submitBtn = this.querySelector('button[type="submit"]');
        if (submitBtn) {
            const originalText = submitBtn.innerHTML;
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i> Agregando...';
            
            try {
                const formData = new FormData(this);
                const response = await fetch(this.action, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'X-CSRFToken': '{{ csrf_token() }}'
                    }
                });
                
                const data = await response.json();
                
                if (!response.ok || !data.success) {
                    throw new Error(data.message || 'Error al agregar al carrito');
                }
                
                showToast(data.message, 'success');
                
                // Actualizar contador del carrito
                const cartCountBadge = document.querySelector('.cart-count');
                if (cartCountBadge) {
                    cartCountBadge.textContent = data.cart_count;
                    cartCountBadge.classList.toggle('d-none', data.cart_count <= 0);
                }
                
            } catch (error) {
                showToast(error.message, 'error');
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalText;
            }
        }
    });
});

//reservas
// Actualización en tiempo real de reservas
const eventSourceReservas = new EventSource('/stream-reservas');
eventSourceReservas.onmessage = function(e) {
    if (e.data === 'actualizar') {
        location.reload();
    }
};

// Manejo del modal para asignar mesas
document.querySelectorAll('.btn-asignar-mesa').forEach(btn => {
    btn.addEventListener('click', function() {
        const reservaId = this.dataset.id;
        const form = document.getElementById('formAsignarMesa');
        form.action = `/reserva/${reservaId}/asignar-mesa`;
        
        const modal = new bootstrap.Modal(document.getElementById('modalAsignarMesa'));
        modal.show();
    });
});

// carro de compras
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.actualizar-cantidad-form').forEach(form => {
        form.addEventListener('submit', async function(e) {
            e.preventDefault();

            const button = e.submitter || document.activeElement;
            const action = button?.getAttribute('data-action') || 'increase';
            const formData = new FormData(this);
            formData.append('action', action);

            // ✅ Leer el token directamente del input oculto del formulario
            const csrfInput = this.querySelector('input[name="csrf_token"]');
            const csrfToken = csrfInput ? csrfInput.value : '';
            formData.append('csrf_token', csrfToken);

            try {
                const response = await fetch(this.action, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-CSRFToken': csrfToken,
                        'Accept': 'application/json'
                    }
                });

                const contentType = response.headers.get('content-type');
                if (!contentType || !contentType.includes('application/json')) {
                    throw new Error('Respuesta no válida. ¿Sesión caducada?');
                }

                const data = await response.json();
                if (!response.ok || !data.success) throw new Error(data.error || 'Error inesperado');

                const cantidadSpan = this.querySelector('.cantidad-actual');
                if (cantidadSpan) cantidadSpan.textContent = data.newQuantity;

                const fila = this.closest('tr');
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
        });
    });
});


// registro de usuario
document.addEventListener('DOMContentLoaded', function() {
    // Mostrar/ocultar contraseña
    const togglePassword = document.getElementById('toggle-password');
    const passwordField = document.getElementById('password');
    const confirmPasswordField = document.getElementById('confirm_password');
    
    togglePassword.addEventListener('click', function() {
        const type = passwordField.getAttribute('type') === 'password' ? 'text' : 'password';
        passwordField.setAttribute('type', type);
        confirmPasswordField.setAttribute('type', type);
        this.classList.toggle('fa-eye-slash');
    });
    
    // Validación de confirmación de email
    const emailField = document.getElementById('email');
    const confirmEmailField = document.getElementById('confirm_email');
    
    confirmEmailField.addEventListener('input', function() {
        if (emailField.value !== confirmEmailField.value) {
            confirmEmailField.classList.add('is-invalid');
        } else {
            confirmEmailField.classList.remove('is-invalid');
        }
    });
    
    // Validación de confirmación de contraseña
    const password = document.getElementById('password');
    const confirmPassword = document.getElementById('confirm_password');
    
    confirmPassword.addEventListener('input', function() {
        if (password.value !== confirmPassword.value) {
            confirmPassword.classList.add('is-invalid');
        } else {
            confirmPassword.classList.remove('is-invalid');
        }
    });
    
    // Validación del formulario antes de enviar
    const form = document.getElementById('registration-form');
    form.addEventListener('submit', function(event) {
        let isValid = true;
        
        // Validar emails coincidan
        if (emailField.value !== confirmEmailField.value) {
            confirmEmailField.classList.add('is-invalid');
            isValid = false;
        }
        
        // Validar contraseñas coincidan
        if (password.value !== confirmPassword.value) {
            confirmPassword.classList.add('is-invalid');
            isValid = false;
        }
        
        // Validar términos aceptados
        if (!document.getElementById('terms').checked) {
            alert('Debes aceptar los términos y condiciones');
            isValid = false;
        }
        
        if (!isValid) {
            event.preventDefault();
            event.stopPropagation();
        }
    });
});





















  
  