/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: '#00674F',
        accent: '#000080',
        bg2: '#0A0A0A',
      },
    },
  },
  plugins: [],
};

