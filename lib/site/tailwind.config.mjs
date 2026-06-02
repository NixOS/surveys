import colors from '@nixos/branding/colors/tailwind.js';

export default {
  darkMode: 'class',
  content: ['./src/**/*.{astro,html,js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors,
    },
  },
};
