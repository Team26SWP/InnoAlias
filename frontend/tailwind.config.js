module.exports = {
  darkMode: 'media',
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",  
  ],
  theme: {
    extend: {
      fontFamily: {
        adlam: ['ADLaM Display', 'Comfortaa'],
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
