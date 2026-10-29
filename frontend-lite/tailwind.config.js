/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js}'],
  theme: {
    extend: {
      colors: {
        primary: '#10B981',
        'primary-deep': '#059669',
        'primary-soft': '#D1FAE5',
        surface: '#FFFFFF',
        'surface-hover': '#F9FAFB',
        ink: '#0F172A',
        'ink-soft': '#64748B',
        'ink-softer': '#94A3B8',
        border: '#E2E8F0',
        error: '#EF4444',
        'error-soft': '#FEE2E2',
      },
    },
  },
  plugins: [],
}
