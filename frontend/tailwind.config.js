/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          dark: '#0a0f1d',
          navy: '#0f172a',
          blue: '#1e3a8a',
          primary: '#2563eb',
          accent: '#4f46e5',
          purple: '#7c3aed',
          light: '#f8fafc',
          card: '#ffffff',
          border: '#e2e8f0',
        },
        status: {
          authentic: '#059669',
          authenticBg: '#ecfdf5',
          authenticBorder: '#a7f3d0',
          modified: '#ea580c',
          modifiedBg: '#fff7ed',
          modifiedBorder: '#fed7aa',
          invalid: '#dc2626',
          invalidBg: '#fef2f2',
          invalidBorder: '#fecaca',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'Courier New', 'monospace']
      }
    },
  },
  plugins: [],
}
