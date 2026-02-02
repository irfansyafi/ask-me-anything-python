// Theme management
const theme = {
  init() {
    this.html = document.documentElement;
    this.toggle = document.getElementById('theme-toggle');
    this.prefersDark = window.matchMedia('(prefers-color-scheme: dark)');
    
    // Set initial theme
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
      this.html.classList.toggle('dark', savedTheme === 'dark');
    } else {
      this.html.classList.toggle('dark', this.prefersDark.matches);
    }

    // Setup listeners
    this.toggle?.addEventListener('click', () => this.toggleTheme());
    this.prefersDark.addEventListener('change', (e) => this.handleSystemThemeChange(e));
  },

  toggleTheme() {
    this.html.classList.toggle('dark');
    localStorage.setItem('theme', this.html.classList.contains('dark') ? 'dark' : 'light');
  },

  handleSystemThemeChange(e) {
    if (!localStorage.getItem('theme')) {
      this.html.classList.toggle('dark', e.matches);
    }
  }
};

// Mobile navigation
const nav = {
  init() {
    this.toggle = document.getElementById('nav-toggle');
    this.menu = document.getElementById('nav-menu');
    
    this.toggle?.addEventListener('click', () => this.toggleMenu());
  },

  toggleMenu() {
    this.menu?.classList.toggle('active');
  }
};

// Space background animation
const space = {
  init() {
    this.container = document.querySelector('.space-bg');
    if (!this.container) return;

    this.createStars();
    window.addEventListener('resize', () => this.createStars());
  },

  createStars() {
    if (!this.container) return;
    
    // Clear existing stars
    this.container.innerHTML = '';
    
    // Calculate number of stars based on viewport
    const count = Math.floor((window.innerWidth * window.innerHeight) / 10000);
    
    for (let i = 0; i < count; i++) {
      const star = document.createElement('div');
      star.className = 'star';
      star.style.left = `${Math.random() * 100}%`;
      star.style.top = `${Math.random() * 100}%`;
      star.style.animationDelay = `${Math.random() * 4}s`;
      this.container.appendChild(star);
    }
  }
};

// Form handling
const forms = {
  init() {
    document.querySelectorAll('form').forEach(form => {
      form.addEventListener('submit', (e) => this.handleSubmit(e));
    });
  },

  async handleSubmit(e) {
    e.preventDefault();
    const form = e.target;
    const data = new FormData(form);
    
    try {
      const response = await fetch(form.action, {
        method: form.method,
        body: data,
        headers: {
          'Accept': 'application/json'
        }
      });
      
      if (response.ok) {
        // Handle success (e.g., show message, clear form)
        form.reset();
      } else {
        throw new Error('Submission failed');
      }
    } catch (error) {
      console.error('Form submission error:', error);
      // Handle error (e.g., show error message)
    }
  }
};

// Initialize everything when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  theme.init();
  nav.init();
  space.init();
  forms.init();
});