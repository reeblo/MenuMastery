// static/js/admin.js
document.addEventListener('DOMContentLoaded', function() {
    // Asegurar que todos los formularios tengan el token CSRF
    document.querySelectorAll('form').forEach(form => {
        // Solo agregar si no existe ya
        if (!form.querySelector('input[name="csrf_token"]')) {
            const csrfInput = document.createElement('input');
            csrfInput.type = 'hidden';
            csrfInput.name = 'csrf_token';
            csrfInput.value = window.csrfToken;
            form.insertBefore(csrfInput, form.firstChild);
        }
    });

    // Interceptar todas las peticiones AJAX
    const originalFetch = window.fetch;
    window.fetch = function(url, options = {}) {
        // Solo agregar CSRF a métodos que lo requieran
        if (options.method && ['POST', 'PUT', 'PATCH', 'DELETE'].includes(options.method.toUpperCase())) {
            options.headers = {
                ...options.headers,
                'X-CSRFToken': window.csrfToken
            };
        }
        return originalFetch(url, options);
    };
});