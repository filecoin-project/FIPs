const colors = require('tailwindcss/colors')

module.exports = {
  purge: ['./src/**/*.js', './src/**/*.liquid'],
  darkMode: 'class',
  theme: {
    colors: { ...colors, transparent: 'transparent', current: 'currentColor' },
    extend: {
      screens: {
        fine: { raw: '(pointer: fine)' },
      },
    },
  },
  variants: {
    extend: {
      scale: ['active'],
    },
  },
  plugins: [require('@tailwindcss/typography')],
}
