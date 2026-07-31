/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      colors: {
        brand: {
          50:  '#f0f4ff',
          100: '#dde6ff',
          200: '#c2d0ff',
          300: '#9cb2ff',
          400: '#7288fc',
          500: '#5060f8',
          600: '#3a3eec',
          700: '#2f2fd1',
          800: '#2929a9',
          900: '#272885',
          950: '#1a1850',
        },
        surface: {
          50:  '#f8f9fc',
          100: '#f1f3fa',
          200: '#e3e8f5',
          800: '#1a1d2e',
          900: '#12141f',
          950: '#0a0b12',
        },
      },
      animation: {
        'fade-in':      'fadeIn 0.4s ease both',
        'slide-up':     'slideUp 0.4s cubic-bezier(0.16,1,0.3,1) both',
        'pulse-slow':   'pulse 3s cubic-bezier(0.4,0,0.6,1) infinite',
        'spin-slow':    'spin 2s linear infinite',
        'shimmer':      'shimmer 1.5s infinite',
        'glow':         'glow 2s ease-in-out infinite alternate',
        'bounce-light': 'bounceDot 1.2s infinite',
      },
      keyframes: {
        fadeIn:   { from: { opacity: '0' }, to: { opacity: '1' } },
        slideUp:  { from: { opacity: '0', transform: 'translateY(16px)' }, to: { opacity: '1', transform: 'translateY(0)' } },
        shimmer:  { '0%': { backgroundPosition: '-200% 0' }, '100%': { backgroundPosition: '200% 0' } },
        glow:     { from: { boxShadow: '0 0 10px rgba(80,96,248,0.3)' }, to: { boxShadow: '0 0 24px rgba(80,96,248,0.6)' } },
        bounceDot: {
          '0%, 80%, 100%': { transform: 'scale(0)', opacity: '0.3' },
          '40%':            { transform: 'scale(1)',   opacity: '1'   },
        },
      },
      backdropBlur: { xs: '2px' },
      boxShadow: {
        'glass':    '0 4px 32px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.05)',
        'glow-sm':  '0 0 12px rgba(80,96,248,0.35)',
        'glow-md':  '0 0 24px rgba(80,96,248,0.45)',
        'card':     '0 2px 12px rgba(0,0,0,0.2)',
        'card-hover': '0 8px 32px rgba(0,0,0,0.35)',
      },
    },
  },
  plugins: [],
}
