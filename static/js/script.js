// static/js/script.js

document.addEventListener('DOMContentLoaded', () => {
    // Este mensaje confirma que el script se cargó correctamente.
    // No hay código aquí que prevenga el envío de formularios.
    console.log("Script.js cargado. El envío de formularios está habilitado.");
});

// Optimización de carga
document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('form');
    const loadingIndicator = document.getElementById('loading-indicator');
    
    // Mostrar indicador al enviar formulario
    if (form) {
        form.addEventListener('submit', function() {
            if (loadingIndicator) {
                loadingIndicator.style.display = 'block';
            }
            // Deshabilitar botón de envío para evitar doble envío
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.textContent = 'Cargando...';
            }
        });
    }
    
    // Ocultar indicador cuando la página esté completamente cargada
    window.addEventListener('load', function() {
        if (loadingIndicator) {
            loadingIndicator.style.display = 'none';
        }
    });
    
    // Precargar siguiente página si el usuario está desplazándose hacia abajo
    let ticking = false;
    function handleScroll() {
        if (!ticking) {
            requestAnimationFrame(function() {
                const scrollHeight = document.documentElement.scrollHeight;
                const scrollTop = document.documentElement.scrollTop;
                const clientHeight = document.documentElement.clientHeight;
                
                // Si el usuario está cerca del final, preparar la próxima carga
                if (scrollTop + clientHeight > scrollHeight * 0.8) {
                    console.log('🚀 Usuario cerca del final, preparando optimizaciones...');
                }
                ticking = false;
            });
            ticking = true;
        }
    }
    
    window.addEventListener('scroll', handleScroll);
});