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

    // Función para mover el carrusel
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
        
        // Reiniciar animaciones
        resetAnimations();
    }

    // Función para reiniciar animaciones
    function resetAnimations() {
        const activeSlide = slideItems[currentIndex];
        const h2 = activeSlide.querySelector('h2');
        const p = activeSlide.querySelector('p');
        const btn = activeSlide.querySelector('.btn');
        
        // Resetear animaciones
        h2.style.animation = 'none';
        p.style.animation = 'none';
        btn.style.animation = 'none';
        
        // Forzar reflow
        void h2.offsetWidth;
        void p.offsetWidth;
        void btn.offsetWidth;
        
        // Reactivar animaciones
        h2.style.animation = 'fadeInUp 0.8s ease';
        p.style.animation = 'fadeInUp 0.8s ease 0.2s forwards';
        btn.style.animation = 'fadeInUp 0.8s ease 0.4s forwards';
    }

    // Event listeners para controles
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

    // Event listeners para indicadores
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























  
  