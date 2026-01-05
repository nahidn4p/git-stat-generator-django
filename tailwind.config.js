/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './dashboard/templates/**/*.html',
    './dashboard/**/*.py',
  ],
  theme: {
    extend: {
      colors: {
        'neon-blue': '#00d4ff',
        'neon-purple': '#b026ff',
        'neon-pink': '#ff006e',
        'dark-bg': '#0a0e27',
        'dark-card': '#141b2d',
        'solar-yellow': '#fdb44b',
        'solar-orange': '#ff6b6b',
      },
      borderRadius: {
        'card': '1.25rem',
        'xl': '1.5rem',
        '2xl': '2rem',
      },
      boxShadow: {
        'card': '0 8px 32px rgba(0, 0, 0, 0.4), 0 4px 16px rgba(0, 0, 0, 0.2)',
        'card-hover': '0 12px 48px rgba(0, 0, 0, 0.5), 0 8px 24px rgba(0, 0, 0, 0.3)',
        'neon': '0 0 20px rgba(0, 212, 255, 0.6), 0 0 40px rgba(0, 212, 255, 0.3)',
        'neon-sm': '0 0 10px rgba(0, 212, 255, 0.5)',
        'glow': '0 0 30px rgba(0, 212, 255, 0.4)',
        'inner-glow': 'inset 0 0 20px rgba(0, 212, 255, 0.1)',
      },
      backdropBlur: {
        'xs': '2px',
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-up': 'slideUp 0.5s ease-out',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        glow: {
          '0%': { boxShadow: '0 0 20px rgba(0, 212, 255, 0.4)' },
          '100%': { boxShadow: '0 0 30px rgba(0, 212, 255, 0.8)' },
        },
      },
      fontFamily: {
        'display': ['Inter', 'system-ui', 'sans-serif'],
        'body': ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}

