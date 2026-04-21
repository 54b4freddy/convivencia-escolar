import type { Config } from 'tailwindcss'

/**
 * Tokens de marca — Arquitectura de Pensamiento.
 * Referencia compartida con `src/index.css` (@theme).
 */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          navy: '#143351',
          emerald: '#009368',
          coral: '#F4A07F',
          sand: '#EED474',
        },
        surface: {
          base: '#FFFFFF',
          card: '#F7F6F2',
          nested: '#ECEAE3',
          dark: '#081828',
        },
      },
      fontFamily: {
        display: ['Playfair Display', 'Georgia', 'serif'],
        body: ['DM Sans', 'system-ui', 'sans-serif'],
        mono: [
          'ui-monospace',
          'SFMono-Regular',
          'Menlo',
          'Monaco',
          'Consolas',
          'monospace',
        ],
      },
      fontSize: {
        display: ['36px', { lineHeight: '1.1', fontWeight: '700' }],
        heading: ['22px', { lineHeight: '1.2', fontWeight: '500' }],
      },
      outlineColor: {
        'brand-emerald': '#009368',
      },
    },
  },
} satisfies Config
