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
          bg: '#F8FAFC',
          primary: '#2563EB',
          'primary-hover': '#1D4ED8',
          accent: '#F97316',
          'accent-hover': '#EA580C',
          text: '#1E293B',
          surface: '#FFFFFF',
          'surface-alt': '#F1F5F9',
          border: '#E2E8F0',
          muted: '#64748B',
        },
        obsidian: {
          950: '#FFFFFF',
          900: '#F8FAFC',
          850: '#F1F5F9',
          800: '#E2E8F0',
          700: '#CBD5E1',
          600: '#94A3B8',
        },
        sapphire: {
          50: '#EFF6FF',
          100: '#DBEAFE',
          200: '#BFDBFE',
          300: '#60A5FA',
          400: '#3B82F6',
          500: '#2563EB',
          600: '#1D4ED8',
          glow: 'rgba(37, 99, 235, 0.15)',
        },
        orange: {
          50: '#FFF7ED',
          100: '#FFEDD5',
          200: '#FED7AA',
          300: '#FDBA74',
          400: '#FB923C',
          500: '#F97316',
          600: '#EA580C',
          700: '#C2410C',
        },
        emerald: {
          50: '#F0FDF4',
          100: '#DCFCE7',
          400: '#22C55E',
          500: '#16A34A',
          600: '#15803D',
          glow: 'rgba(22, 163, 74, 0.15)',
        },
        crimson: {
          50: '#FEF2F2',
          100: '#FEE2E2',
          400: '#EF4444',
          500: '#DC2626',
          600: '#B91C1C',
          glow: 'rgba(220, 38, 38, 0.15)',
        },
        amber: {
          50: '#FFFBEB',
          100: '#FEF3C7',
          400: '#FBBF24',
          500: '#F59E0B',
          600: '#D97706',
          glow: 'rgba(245, 158, 11, 0.15)',
        },
        cyan: {
          400: '#38BDF8',
          500: '#0EA5E9',
          600: '#0284C7',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace']
      }
    },
  },
  plugins: [],
}
