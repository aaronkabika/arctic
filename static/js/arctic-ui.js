/* ==========================================
   ARCTIC UI - JavaScript Moderne
   Interactions fluides et composants réactifs
   ========================================== */

class ArcticUI {
    constructor() {
        this.init();
    }

    init() {
        this.initFlashMessages();
        this.initScrollEffects();
        this.initCardAnimations();
        this.initFormEnhancements();
        this.initDecorativeElements();
        this.initLazyLoading();
        this.initAccessibility();
    }

    /* =========================
       MESSAGES FLASH
       ========================= */
    
    initFlashMessages() {
        const flashMessages = document.querySelectorAll('.flash-message');
        
        flashMessages.forEach(message => {
            // Animation d'entrée
            message.style.opacity = '0';
            message.style.transform = 'translateY(-20px)';
            
            requestAnimationFrame(() => {
                message.style.transition = 'all 0.3s ease-out';
                message.style.opacity = '1';
                message.style.transform = 'translateY(0)';
            });
            
            // Auto-hide après 5 secondes
            setTimeout(() => {
                this.hideFlashMessage(message);
            }, 5000);
            
            // Bouton de fermeture
            const closeBtn = message.querySelector('.flash-close');
            if (closeBtn) {
                closeBtn.addEventListener('click', () => {
                    this.hideFlashMessage(message);
                });
            }
        });
    }

    hideFlashMessage(message) {
        message.style.opacity = '0';
        message.style.transform = 'translateY(-20px)';
        
        setTimeout(() => {
            message.remove();
        }, 300);
    }

    /* =========================
       EFFETS DE SCROLL
       ========================= */
    
    initScrollEffects() {
        // Navbar transparente au scroll
        const navbar = document.querySelector('.navbar');
        if (navbar) {
            window.addEventListener('scroll', () => {
                if (window.scrollY > 50) {
                    navbar.classList.add('navbar-scrolled');
                } else {
                    navbar.classList.remove('navbar-scrolled');
                }
            });
        }

        // Animations au scroll (Intersection Observer)
        const observerOptions = {
            root: null,
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-in');
                    observer.unobserve(entry.target);
                }
            });
        }, observerOptions);

        // Observer les éléments avec data-animate
        const animateElements = document.querySelectorAll('[data-animate]');
        animateElements.forEach(el => {
            el.style.opacity = '0';
            el.style.transform = 'translateY(30px)';
            el.style.transition = 'all 0.6s cubic-bezier(0.4, 0, 0.2, 1)';
            observer.observe(el);
        });
    }

    /* =========================
       ANIMATIONS DE CARTES
       ========================= */
    
    initCardAnimations() {
        const cards = document.querySelectorAll('.card-interactive');
        
        cards.forEach(card => {
            // Effet de parallaxe au survol
            card.addEventListener('mousemove', (e) => {
                const rect = card.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;
                
                const centerX = rect.width / 2;
                const centerY = rect.height / 2;
                
                const rotateX = (y - centerY) / 20;
                const rotateY = (centerX - x) / 20;
                
                card.style.transform = `
                    perspective(1000px)
                    rotateX(${rotateX}deg)
                    rotateY(${rotateY}deg)
                    translateY(-6px)
                    scale(1.02)
                `;
            });
            
            card.addEventListener('mouseleave', () => {
                card.style.transform = 'none';
            });
        });
    }

    /* =========================
       AMÉLIORATIONS DE FORMULAIRES
       ========================= */
    
    initFormEnhancements() {
        // Labels flottants
        const inputs = document.querySelectorAll('.input, .textarea, .select');
        
        inputs.forEach(input => {
            if (input.value) {
                input.classList.add('has-value');
            }
            
            input.addEventListener('input', () => {
                if (input.value) {
                    input.classList.add('has-value');
                } else {
                    input.classList.remove('has-value');
                }
            });
            
            input.addEventListener('blur', () => {
                if (!input.value) {
                    input.classList.remove('has-value');
                }
            });
        });

        // Indicateur de force du mot de passe
        const passwordInputs = document.querySelectorAll('input[type="password"]');
        
        passwordInputs.forEach(input => {
            const strengthIndicator = document.createElement('div');
            strengthIndicator.className = 'password-strength';
            strengthIndicator.innerHTML = `
                <div class="strength-bar">
                    <div class="strength-fill"></div>
                </div>
                <span class="strength-text"></span>
            `;
            
            if (input.id === 'password' || input.name === 'password') {
                input.parentNode.appendChild(strengthIndicator);
                
                input.addEventListener('input', () => {
                    this.updatePasswordStrength(input.value, strengthIndicator);
                });
            }
        });

        // Preview des images uploadées
        const fileInputs = document.querySelectorAll('input[type="file"]');
        
        fileInputs.forEach(input => {
            if (input.accept && input.accept.includes('image')) {
                input.addEventListener('change', (e) => {
                    this.previewImages(e.target);
                });
            }
        });
    }

    updatePasswordStrength(password, indicator) {
        const fill = indicator.querySelector('.strength-fill');
        const text = indicator.querySelector('.strength-text');
        
        let strength = 0;
        let message = '';
        
        if (password.length >= 8) strength++;
        if (password.match(/[a-z]/)) strength++;
        if (password.match(/[A-Z]/)) strength++;
        if (password.match(/[0-9]/)) strength++;
        if (password.match(/[^a-zA-Z0-9]/)) strength++;
        
        const percentage = (strength / 5) * 100;
        fill.style.width = `${percentage}%`;
        
        if (strength < 2) {
            fill.style.background = '#FA663D';
            text.textContent = 'Faible';
            text.style.color = '#FA663D';
        } else if (strength < 4) {
            fill.style.background = '#FCB61C';
            text.textContent = 'Moyen';
            text.style.color = '#FCB61C';
        } else {
            fill.style.background = '#7CEC98';
            text.textContent = 'Fort';
            text.style.color = '#456B50';
        }
    }

    previewImages(input) {
        const preview = input.parentNode.querySelector('.image-preview') || this.createPreviewContainer(input);
        preview.innerHTML = '';
        
        const files = Array.from(input.files);
        
        files.forEach(file => {
            if (file.type.startsWith('image/')) {
                const reader = new FileReader();
                
                reader.onload = (e) => {
                    const img = document.createElement('img');
                    img.src = e.target.result;
                    img.className = 'preview-image';
                    img.style.cssText = `
                        width: 120px;
                        height: 120px;
                        object-fit: cover;
                        border-radius: var(--radius-lg);
                        box-shadow: var(--shadow-md);
                    `;
                    
                    preview.appendChild(img);
                };
                
                reader.readAsDataURL(file);
            }
        });
    }

    createPreviewContainer(input) {
        const preview = document.createElement('div');
        preview.className = 'image-preview';
        preview.style.cssText = `
            display: flex;
            flex-wrap: wrap;
            gap: var(--space-3);
            margin-top: var(--space-4);
        `;
        
        input.parentNode.appendChild(preview);
        return preview;
    }

    /* =========================
       ÉLÉMENTS DÉCORATIFS ANIMÉS
       ========================= */
    
    initDecorativeElements() {
        // Créer des formes géométriques flottantes
        const createFloatingShape = (type, container) => {
            const shape = document.createElement('div');
            shape.className = `decorative-shape shape-${type}`;
            
            const size = Math.random() * 100 + 50;
            const x = Math.random() * 100;
            const y = Math.random() * 100;
            const duration = Math.random() * 20 + 10;
            const delay = Math.random() * 5;
            
            shape.style.cssText = `
                width: ${size}px;
                height: ${size}px;
                left: ${x}%;
                top: ${y}%;
                opacity: ${Math.random() * 0.1 + 0.05};
                animation: float ${duration}s ${delay}s infinite ease-in-out;
            `;
            
            container.appendChild(shape);
        };

        // Ajouter des formes aux sections hero
        const heroSections = document.querySelectorAll('.hero, .artist-welcome, .visitor-hero');
        
        heroSections.forEach(hero => {
            // Créer 3-5 formes aléatoires
            const shapeCount = Math.floor(Math.random() * 3) + 3;
            const shapes = ['circle', 'square'];
            
            for (let i = 0; i < shapeCount; i++) {
                const shapeType = shapes[Math.floor(Math.random() * shapes.length)];
                createFloatingShape(shapeType, hero);
            }
        });

        // Animation CSS pour les formes
        if (!document.getElementById('arctic-animations')) {
            const style = document.createElement('style');
            style.id = 'arctic-animations';
            style.textContent = `
                @keyframes float {
                    0%, 100% {
                        transform: translate(0, 0) rotate(0deg);
                    }
                    25% {
                        transform: translate(10px, -20px) rotate(5deg);
                    }
                    50% {
                        transform: translate(-10px, -40px) rotate(-5deg);
                    }
                    75% {
                        transform: translate(-20px, -20px) rotate(5deg);
                    }
                }
                
                @keyframes animate-in {
                    to {
                        opacity: 1;
                        transform: translateY(0);
                    }
                }
                
                .animate-in {
                    animation: animate-in 0.6s cubic-bezier(0.4, 0, 0.2, 1) forwards;
                }
            `;
            document.head.appendChild(style);
        }
    }

    /* =========================
       LAZY LOADING D'IMAGES
       ========================= */
    
    initLazyLoading() {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    
                    if (img.dataset.src) {
                        img.src = img.dataset.src;
                        img.removeAttribute('data-src');
                        img.classList.add('loaded');
                    }
                    
                    observer.unobserve(img);
                }
            });
        });

        const lazyImages = document.querySelectorAll('img[data-src]');
        lazyImages.forEach(img => imageObserver.observe(img));
    }

    /* =========================
       ACCESSIBILITÉ
       ========================= */
    
    initAccessibility() {
        // Navigation au clavier améliorée
        document.addEventListener('keydown', (e) => {
            // Escape pour fermer les modals/dropdowns
            if (e.key === 'Escape') {
                const activeModal = document.querySelector('.modal.active');
                if (activeModal) {
                    activeModal.classList.remove('active');
                }
            }
        });

        // Focus visible pour la navigation au clavier
        document.addEventListener('mousedown', () => {
            document.body.classList.add('using-mouse');
        });

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Tab') {
                document.body.classList.remove('using-mouse');
            }
        });

        // Skip link
        const skipLink = document.querySelector('.skip-link');
        if (skipLink) {
            skipLink.addEventListener('click', (e) => {
                e.preventDefault();
                const target = document.querySelector(skipLink.getAttribute('href'));
                if (target) {
                    target.setAttribute('tabindex', '-1');
                    target.focus();
                }
            });
        }
    }
}

// Utilitaires globaux

const ArcticUtils = {
    // Debounce pour optimiser les événements
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    // Throttle pour limiter les appels
    throttle(func, limit) {
        let inThrottle;
        return function(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    },

    // Formater les prix
    formatPrice(price) {
        return new Intl.NumberFormat('fr-CD', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 2
        }).format(price);
    },

    // Formater les dates
    formatDate(date) {
        return new Intl.DateTimeFormat('fr-FR', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        }).format(new Date(date));
    },

    // Copier dans le presse-papier
    async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            return true;
        } catch (err) {
            console.error('Erreur de copie:', err);
            return false;
        }
    },

    // Partage natif
    async share(data) {
        if (navigator.share) {
            try {
                await navigator.share(data);
                return true;
            } catch (err) {
                console.error('Erreur de partage:', err);
                return false;
            }
        }
        return false;
    }
};

// Initialiser Arctic UI au chargement du DOM
document.addEventListener('DOMContentLoaded', () => {
    new ArcticUI();
});

// Export pour utilisation dans d'autres scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ArcticUI, ArcticUtils };
}
