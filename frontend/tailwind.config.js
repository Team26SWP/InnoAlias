module.exports = {
  darkMode: 'class',
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",  
  ],
  theme: {
    extend: {
      fontFamily: {
        adlam: ['Comfortaa', 'sans-serif'],
      },
      colors: {
        background: '#FAF6E9',
        primary:    '#1E6DB9',
        accent:     '#DBD9D1',
        darkbg: '#1A1A1A',
      }
    },
  },
  plugins: [],
}
