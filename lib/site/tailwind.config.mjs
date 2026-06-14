import colors from '@nixos/branding/colors/tailwind.js';
import defaultTheme from 'tailwindcss/defaultTheme';

export default {
  darkMode: 'class',
  content: ['./src/**/*.{astro,html,js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors,
      fontFamily: {
        sans: ['Roboto Flex Variable', ...defaultTheme.fontFamily.sans],
        heading: ['Route159', ...defaultTheme.fontFamily.sans],
      },
    },
  },
};
