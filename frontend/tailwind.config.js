/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        mono: ['"Fira Code"', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'monospace'],
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
      colors: {
        trading: {
          bg: '#0B0E14',      // Deep terminal background
          panel: '#151924',   // Elevated panel background
          border: '#2B313F',  // Subtle borders
          text: '#A0AEC0',    // Muted text
          green: '#00C853',   // Profit/Buy
          red: '#FF3D00',     // Loss/Sell
          blue: '#2962FF'     // Info/Action
        }
      }
    },
  },
  plugins: [],
}