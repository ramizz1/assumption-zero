/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        surface: '#fafafa',
        card: '#ffffff',
        border: '#e5e5e5',
        verseo: {
          bg: '#f9f9f9',
          card: '#ffffff',
          accent: '#181818',
          border: 'rgba(0, 0, 0, 0.08)',
          grid: 'rgba(0, 0, 0, 0.04)',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        display: ['Space Grotesk', 'Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
    },
  },
  plugins: [],
}
