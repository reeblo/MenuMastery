// Funciones comunes para empleados
document.addEventListener('DOMContentLoaded', function() {
    // 1. Toggle del menú lateral
    const menuToggle = document.querySelector('.menu-toggle');
    if (menuToggle) {
        menuToggle.addEventListener('click', () => {
            document.querySelector('.empleado-sidebar').classList.toggle('active');
        });
    }

    // 2. Sistema de notificaciones (solo para empleados)
    if (document.getElementById('empleado-notifications')) {
        initNotificationSystem();
    }

    // 3. Confirmaciones de acciones
    document.querySelectorAll('.btn-marcar-entregado, .btn-marcar-list').forEach(btn => {
        btn.addEventListener('click', function(e) {
            if (!confirm(this.getAttribute('data-confirm') || '¿Está seguro?')) {
                e.preventDefault();
            }
        });
    });

    // 4. Procesar mensajes flash
    processFlashMessages();
});

// Sistema de notificaciones mejorado
function initNotificationSystem() {
    // Conexión SSE
    const eventSource = new EventSource('/stream-pedidos');
    
    eventSource.onmessage = (e) => {
        if (e.data === 'actualizar') {
            showToast('¡Nuevo pedido recibido!', 'success');
            updateNotificationBadge();
        }
    };
    
    eventSource.onerror = () => {
        console.log('Reconectando SSE...');
        setTimeout(initNotificationSystem, 5000);
    };
}

// Actualizar badge de notificaciones
async function updateNotificationBadge() {
    try {
        const response = await fetch('/notificaciones/no-vistas');
        const data = await response.json();
        
        const badge = document.querySelector('.notification-badge') || 
                    createNotificationBadge();
        
        if (data.count > 0) {
            badge.textContent = data.count;
            badge.style.display = 'inline-block';
        } else {
            badge.style.display = 'none';
        }
    } catch (error) {
        console.error('Error actualizando notificaciones:', error);
    }
}

function createNotificationBadge() {
    const btn = document.querySelector('.btn-notification');
    const badge = document.createElement('span');
    badge.className = 'notification-badge';
    badge.style.display = 'none';
    btn.appendChild(badge);
    return badge;
}

// Función toast mejorada
function showToast(message, type = 'success') {
    const toastContainer = document.getElementById('toast-container') || createToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast show align-items-center text-white bg-${type}`;
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    setupToastAutoDismiss(toast);
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 1100;
    `;
    document.body.appendChild(container);
    return container;   
}

function setupToastAutoDismiss(toast) {
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Procesar mensajes flash
function processFlashMessages() {
    document.querySelectorAll('.alert').forEach(alert => {
        const type = alert.classList.contains('alert-danger') ? 'danger' : 
                    alert.classList.contains('alert-warning') ? 'warning' : 
                    'success';
        showToast(alert.textContent.trim(), type);
        alert.remove();
    });
}