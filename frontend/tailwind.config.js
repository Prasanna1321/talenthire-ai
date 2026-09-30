/** Belongs in: frontend/tailwind.config.js */
/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#eef4ff',
          100: '#d9e6ff',
          200: '#b3ccff',
          300: '#82a9ff',
          400: '#5480ff',
          500: '#2f56f5',
          600: '#1f3fd6',
          700: '#1a32ab',
          800: '#182c89',
          900: '#182a6f',
        },
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
