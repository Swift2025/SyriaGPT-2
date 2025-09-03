/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
    './src/context/**/*.{js,ts,jsx,tsx,mdx}',
    './services/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      // خطوط مخصصة للعربية
      fontFamily: {
        'arabic': ['Noto Sans Arabic', 'Cairo', 'Tajawal', 'system-ui', 'sans-serif'],
        'english': ['Inter', 'system-ui', 'sans-serif'],
      },
      
      // ألوان العلامة التجارية من Figma
      colors: {
        // ألوان العلامة التجارية الرئيسية
        brand: {
          // الألوان الأساسية من Figma
          'teal-primary': 'rgb(66 129 119)',     // #428177
          'teal-dark': 'rgb(5 66 57)',           // #054239
          'gold-primary': 'rgb(185 167 121)',    // #b9a779
          
          // ألوان الخلفية
          'cream': 'rgb(217 217 217)',           // #D9D9D9
          'navy-dark': 'rgb(0 35 38)',           // #002326
          
          // ألوان النصوص
          'text-dark': 'rgb(22 22 22)',          // #161616
          'text-gray': 'rgb(61 58 59)',          // #3d3a3b
        },
        
        // ألوان سورية رسمية (للمرجع)
        syria: {
          red: '#CE1126',
          white: '#FFFFFF',
          black: '#000000',
          green: '#007A3D',
        },
        
        // ألوان Tailwind المحسنة
        teal: {
          50: '#f0fdfa',
          100: '#ccfbf1',
          200: '#99f6e4',
          300: '#5eead4',
          400: '#2dd4bf',
          500: 'rgb(66 129 119)',   // brand-teal-primary
          600: 'rgb(5 66 57)',      // brand-teal-dark
          700: '#0f766e',
          800: '#115e59',
          900: '#134e4a',
        },
        
        amber: {
          50: '#D9D9D9',
          100: '#b9a779d5',
          200: '#428177',
          300: '#428177',
          400: '#428177',
          500: '#428177',
          600: '#428177',  
          700: '#0f766e',
          800: '#115e59',
          900: '#134e4a',
        },

        // ألوان النظام
        gray: {
          50: '#f9fafb',
          100: '#f3f4f6',
          200: 'rgb(217 217 217)',  // brand-cream
          300: '#d1d5db',
          400: '#9ca3af',
          500: '#6b7280',
          600: 'rgb(61 58 59)',     // brand-text-gray
          700: '#374151',
          800: 'rgb(22 22 22)',     // brand-text-dark
          900: 'rgb(0 35 38)',      // brand-navy-dark
        }
      },
      
      // مسافات مخصصة للتخطيط العربي
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
        '128': '32rem',
      },
      
      // خصائص للرسوم المتحركة
      animation: {
        'bounce-slow': 'bounce 2s infinite',
        'pulse-slow': 'pulse 3s infinite',
        'fade-in': 'fadeIn 0.3s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'typing': 'typing 1.5s infinite',
        'float': 'float 3s ease-in-out infinite',
      },
      
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideUp: {
          '0%': { transform: 'translateY(100%)' },
          '100%': { transform: 'translateY(0)' },
        },
        typing: {
          '0%, 60%, 100%': { transform: 'translateY(0)' },
          '30%': { transform: 'translateY(-10px)' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-10px)' },
        }
      },
      
      // خصائص للظلال المخصصة
      boxShadow: {
        'soft': '0 2px 15px 0 rgba(0, 0, 0, 0.05)',
        'medium': '0 4px 20px 0 rgba(0, 0, 0, 0.1)',
        'strong': '0 10px 40px 0 rgba(0, 0, 0, 0.15)',
        'glow': '0 0 20px rgba(66, 129, 119, 0.3)',
      },
      
      // نقاط التوقف المخصصة
      screens: {
        'xs': '375px',
        'sm': '640px',
        'md': '768px',
        'lg': '1024px',
        'xl': '1280px',
        '2xl': '1536px',
      },
      
      // أحجام الخطوط المحسنة للعربية
      fontSize: {
        'xs': ['0.75rem', { lineHeight: '1.5' }],
        'sm': ['0.875rem', { lineHeight: '1.6' }],
        'base': ['1rem', { lineHeight: '1.7' }],
        'lg': ['1.125rem', { lineHeight: '1.7' }],
        'xl': ['1.25rem', { lineHeight: '1.7' }],
        '2xl': ['1.5rem', { lineHeight: '1.6' }],
        '3xl': ['1.875rem', { lineHeight: '1.5' }],
        '4xl': ['2.25rem', { lineHeight: '1.4' }],
      },

      // متغيرات للشبكة والتخطيط
      gridTemplateColumns: {
        'suggestions': 'repeat(auto-fit, minmax(280px, 1fr))',
      },
    },
  },
  plugins: [
    // إضافة plugin للطباعة المحسنة
    require('@tailwindcss/typography'),
    
    // Plugin مخصص لدعم RTL والألوان
    function({ addUtilities, addBase, addComponents, theme }) {
      // إضافة أنماط أساسية للعربية
      addBase({
        'html': {
          fontFamily: theme('fontFamily.arabic'),
          scrollBehavior: 'smooth',
        },
        'body': {
          fontFamily: theme('fontFamily.arabic'),
          lineHeight: '1.7',
          fontFeatureSettings: '"kern" 1',
        },
        '[dir="rtl"]': {
          textAlign: 'right',
        },
        '[dir="ltr"]': {
          textAlign: 'left',
        },
        // تحسين عرض الخطوط العربية
        '.arabic-text': {
          fontFamily: theme('fontFamily.arabic'),
          fontWeight: '400',
          letterSpacing: '0.01em',
        },
      });

      // مكونات قابلة لإعادة الاستخدام
      addComponents({
        '.suggestion-card': {
          padding: '1rem',
          backgroundColor: 'rgb(66 129 119)',
          color: 'white',
          borderRadius: '0.5rem',
          textAlign: 'center',
          minHeight: '80px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '0.875rem',
          lineHeight: '1.25rem',
          transition: 'all 0.2s ease',
          cursor: 'pointer',
          '&:hover': {
            backgroundColor: 'rgb(5 66 57)',
            transform: 'translateY(-2px)',
            boxShadow: theme('boxShadow.glow'),
          },
        },
        '.message-bubble': {
          padding: '0.75rem 1rem',
          borderRadius: '1rem',
          marginBottom: '0.5rem',
          wordWrap: 'break-word',
          lineHeight: '1.6',
          animation: 'fadeIn 0.3s ease-out',
        },
        '.chat-input': {
          backgroundColor: 'rgba(255, 255, 255, 0.9)',
          borderRadius: '9999px',
          border: '1px solid rgba(0, 0, 0, 0.1)',
          padding: '0.5rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem',
          transition: 'all 0.2s ease',
          '&:focus-within': {
            borderColor: 'rgb(66 129 119)',
            boxShadow: '0 0 0 3px rgba(66, 129, 119, 0.1)',
          },
        },
        '.sidebar-button': {
          width: '100%',
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem',
          padding: '0.5rem',
          borderRadius: '0.5rem',
          fontSize: '0.875rem',
          transition: 'all 0.2s ease',
          color: 'rgba(255, 255, 255, 0.9)',
          '&:hover': {
            backgroundColor: 'rgba(255, 255, 255, 0.1)',
            color: 'white',
          },
        },
      });
      
      // أدوات مساعدة للـ RTL
      addUtilities({
        '.rtl-flip': {
          transform: 'scaleX(-1)',
        },
        '.text-start': {
          textAlign: 'start',
        },
        '.text-end': {
          textAlign: 'end',
        },
        // مسافات للـ RTL
        '.me-auto': {
          marginInlineEnd: 'auto',
        },
        '.ms-auto': {
          marginInlineStart: 'auto',
        },
        '.pe-4': {
          paddingInlineEnd: '1rem',
        },
        '.ps-4': {
          paddingInlineStart: '1rem',
        },
        // محاذاة عائمة للـ RTL
        '.float-start': {
          float: 'inline-start',
        },
        '.float-end': {
          float: 'inline-end',
        },
        // أنماط التحميل
        '.loading-dots': {
          display: 'inline-flex',
          gap: '0.25rem',
        },
        '.loading-dot': {
          width: '0.5rem',
          height: '0.5rem',
          backgroundColor: theme('colors.gray.500'),
          borderRadius: '50%',
          animation: 'typing 1.5s infinite',
        },
        // تحسينات الأداء
        '.smooth-scroll': {
          scrollBehavior: 'smooth',
        },
        '.gpu-accelerated': {
          transform: 'translateZ(0)',
          willChange: 'transform',
        },
        // أنماط الانتقال المخصصة
        '.transition-theme': {
          transition: 'background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease',
        },
      });
    }
  ],
}