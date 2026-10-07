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
        background: '#090d16',
        panel: '#0f172a',
        'panel-accent': '#1e293b',
        'panel-border': '#334155',
        // Semantic operations tokens
        sev1: {
          DEFAULT: '#ef4444',
          bg: '#450a0a',
          text: '#fecaca',
          border: '#b91c1c'
        },
        sev2: {
          DEFAULT: '#f97316',
          bg: '#431407',
          text: '#fed7aa',
          border: '#c2410c'
        },
        sev3: {
          DEFAULT: '#eab308',
          bg: '#422006',
          text: '#fef08a',
          border: '#a16207'
        },
        sev4: {
          DEFAULT: '#3b82f6',
          bg: '#172554',
          text: '#bfdbfe',
          border: '#1d4ed8'
        },
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Menlo', 'Monaco', 'Courier New', 'monospace'],
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
