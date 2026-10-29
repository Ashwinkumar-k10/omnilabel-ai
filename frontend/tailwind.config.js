/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        midnight: '#0B1220',
        navy: '#111827',
        'surface-secondary': '#172033',
        'surface-elevated': '#1E293B',
        'border-subtle': '#334155',
        'text-primary': '#F8FAFC',
        'text-secondary': '#CBD5E1',
        'text-muted': '#94A3B8',
        'clinical-teal': {
          DEFAULT: '#0F766E',
          bright: '#14B8A6',
          hover: '#0D9488',
          dark: '#115E59',
        },
        'clinical-blue': {
          DEFAULT: '#2563EB',
          light: '#60A5FA',
          hover: '#1D4ED8',
          dark: '#1E40AF',
        },
        status: {
          success: '#34D399',
          warning: '#FBBF24',
          danger: '#F87171',
          info: '#38BDF8',
        }
      },
      backgroundImage: {
        'brand-gradient': 'linear-gradient(110deg, #0F766E 0%, #0D9488 50%, #2563EB 100%)',
        'hero-gradient': 'linear-gradient(90deg, #FFFFFF 0%, #CBD5E1 65%, #5EEAD4 100%)',
      }
    },
  },
  plugins: [],
};
