/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Primary Colors
        'primary': '#1E40AF', // Deep blue (primary) - blue-800
        'primary-50': '#EFF6FF', // Very light blue - blue-50
        'primary-100': '#DBEAFE', // Light blue - blue-100
        'primary-500': '#3B82F6', // Medium blue - blue-500
        'primary-600': '#2563EB', // Darker blue - blue-600
        'primary-700': '#1D4ED8', // Dark blue - blue-700
        
        // Secondary Colors
        'secondary': '#7C3AED', // Intelligent purple (secondary) - violet-600
        'secondary-50': '#F5F3FF', // Very light purple - violet-50
        'secondary-100': '#EDE9FE', // Light purple - violet-100
        'secondary-500': '#8B5CF6', // Medium purple - violet-500
        
        // Accent Colors
        'accent': '#F59E0B', // Warm amber (accent) - amber-500
        'accent-50': '#FFFBEB', // Very light amber - amber-50
        'accent-100': '#FEF3C7', // Light amber - amber-100
        'accent-600': '#D97706', // Darker amber - amber-600
        
        // Background Colors
        'background': '#FAFBFC', // Soft off-white (background) - gray-50
        'surface': '#FFFFFF', // Pure white (surface) - white
        
        // Text Colors
        'text-primary': '#1F2937', // Rich charcoal (text primary) - gray-800
        'text-secondary': '#6B7280', // Balanced gray (text secondary) - gray-500
        'text-muted': '#9CA3AF', // Light gray for muted text - gray-400
        
        // Status Colors
        'success': '#10B981', // Encouraging green (success) - emerald-500
        'success-50': '#ECFDF5', // Very light green - emerald-50
        'success-100': '#D1FAE5', // Light green - emerald-100
        
        'warning': '#F59E0B', // Constructive amber (warning) - amber-500
        'warning-50': '#FFFBEB', // Very light amber - amber-50
        'warning-100': '#FEF3C7', // Light amber - amber-100
        
        'error': '#EF4444', // Clear red (error) - red-500
        'error-50': '#FEF2F2', // Very light red - red-50
        'error-100': '#FEE2E2', // Light red - red-100
        
        // Border Colors
        'border': '#E5E7EB', // Minimal border color - gray-200
        'border-light': '#F3F4F6', // Light border - gray-100
      },
      fontFamily: {
        'sans': ['Source Sans Pro', 'sans-serif'],
        'heading': ['Inter', 'sans-serif'],
        'data': ['JetBrains Mono', 'monospace'],
      },
      fontSize: {
        'xs': ['0.75rem', { lineHeight: '1rem' }],
        'sm': ['0.875rem', { lineHeight: '1.25rem' }],
        'base': ['1rem', { lineHeight: '1.5rem' }],
        'lg': ['1.125rem', { lineHeight: '1.75rem' }],
        'xl': ['1.25rem', { lineHeight: '1.75rem' }],
        '2xl': ['1.5rem', { lineHeight: '2rem' }],
        '3xl': ['1.875rem', { lineHeight: '2.25rem' }],
        '4xl': ['2.25rem', { lineHeight: '2.5rem' }],
      },
      boxShadow: {
        'subtle': '0 1px 3px rgba(0, 0, 0, 0.1)',
        'card': '0 4px 6px rgba(0, 0, 0, 0.1)',
        'elevated': '0 8px 25px rgba(0, 0, 0, 0.15)',
      },
      borderRadius: {
        'DEFAULT': '8px',
        'sm': '4px',
        'lg': '12px',
        'xl': '16px',
      },
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
        '240': '60rem',
      },
      zIndex: {
        '800': '800',
        '900': '900',
        '1000': '1000',
        '1100': '1100',
      },
      animation: {
        'ai-pulse': 'ai-pulse 2s ease-in-out infinite',
        'shimmer': 'shimmer 1.5s infinite',
      },
      keyframes: {
        'ai-pulse': {
          '0%, 100%': { opacity: '0.4' },
          '50%': { opacity: '1' },
        },
        'shimmer': {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
      },
      backdropBlur: {
        'subtle': '8px',
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
    require('@tailwindcss/forms'),
  ],
}