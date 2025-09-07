// src/app/[lang]/components/ClientLayout.tsx
'use client';

import React, { useState, useEffect } from 'react';
import { Toaster } from 'react-hot-toast';
import Sidebar from './Sidebar';
import { AuthProvider, useAuth } from '../../../context/AuthContext';

// مكون داخلي لإدارة المحتوى الرئيسي وشاشة التحميل
const MainAppContent = ({ children, dictionary }: { children: React.ReactNode; dictionary: any }) => {
  const { user, isLoading: isAuthLoading } = useAuth();
  const [isMounted, setIsMounted] = useState(false);
  
  // Debug: مراقبة حالة المصادقة
  useEffect(() => {
    console.log('ClientLayout - Auth state:', { user, isAuthLoading });
    if (user) {
      console.log('ClientLayout - User details:', {
        id: user.id,
        email: user.email,
        full_name: user.full_name,
        name: user.name
      });
    }
  }, [user, isAuthLoading]);

  // تهيئة الحالة من localStorage أو من إعدادات النظام
  const [darkMode, setDarkMode] = useState(false); // القيمة الافتراضية للخادم

  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  useEffect(() => {
    setIsMounted(true);
    
    // تحميل الثيم من localStorage بعد التحميل
    if (typeof window !== 'undefined') {
      const savedTheme = localStorage.getItem('theme');
      if (savedTheme) {
        setDarkMode(savedTheme === 'dark');
      } else {
        setDarkMode(window.matchMedia('(prefers-color-scheme: dark)').matches);
      }
    }
  }, []);

  // تأثير مسؤول عن الانتقال السلس من شاشة التحميل إلى التطبيق
  useEffect(() => {
    if (!isAuthLoading && isMounted && typeof window !== 'undefined') {
      const loader = document.getElementById('initial-loader');
      const content = document.getElementById('app-content');
      if (loader) {
        loader.style.opacity = '0';
        setTimeout(() => {
          loader.style.display = 'none';
        }, 300);
      }
      if (content) {
        content.style.opacity = '1';
      }
    }
  }, [isAuthLoading, isMounted]);

  // تحديث localStorage و class في <html> عند تغيير الثيم
  useEffect(() => {
    if (typeof window !== 'undefined' && isMounted) {
      const root = window.document.documentElement;
      const newTheme = darkMode ? 'dark' : 'light';
      root.classList.remove('light', 'dark');
      root.classList.add(newTheme);
      localStorage.setItem('theme', newTheme);
    }
  }, [darkMode, isMounted]);

  return (
    <>
      <div id="initial-loader" className="fixed inset-0 bg-brand-cream dark:bg-brand-navy-dark z-[100] flex items-center justify-center transition-opacity duration-300" suppressHydrationWarning={true}>
        <div className="text-center" suppressHydrationWarning={true}>
          <div className="w-16 h-16 mx-auto mb-4 animate-pulse" suppressHydrationWarning={true}>
            <img src="/logo.ai.svg" alt="Syrian Eagle Logo" className="w-full h-full" />
          </div>
          <h2 className="text-xl font-semibold text-brand-gold-primary mb-2">{dictionary.loader?.title || 'Welcome to SyriaGPT'}</h2>
          <p className="text-sm text-brand-text-gray dark:text-gray-400">{dictionary.loader?.loading || 'Loading...'}</p>
        </div>
      </div>

      <main id="app-content" className="opacity-0 transition-opacity duration-300">
        <div className="flex h-screen bg-brand-cream dark:bg-brand-navy-dark" suppressHydrationWarning={true}>
          <Sidebar
            dictionary={dictionary}
            darkMode={darkMode}
            toggleDarkMode={() => setDarkMode(!darkMode)}
            isSidebarOpen={isSidebarOpen}
            setIsSidebarOpen={setIsSidebarOpen}
          />
          <div className="flex-1 overflow-y-auto">
            {React.isValidElement(children) 
              ? React.cloneElement(children as React.ReactElement<any>, { toggleSidebar: () => setIsSidebarOpen(!isSidebarOpen) }) 
              : children
            }
          </div>
        </div>
      </main>
    </>
  );
};

// المكون الرئيسي الذي يقوم بتوفير AuthContext
export default function ClientLayout({ children, dictionary }: { children: React.ReactNode; dictionary: any }) {
  return (
    <AuthProvider>
      <Toaster
        position="top-center"
        reverseOrder={false}
        toastOptions={{
          className: 'font-arabic border border-black/10 dark:border-white/10',
          style: { borderRadius: '10px', background: '#3d3a3b', color: '#D9D9D9' },
          success: { duration: 3000, iconTheme: { primary: '#428177', secondary: 'white' } },
          error: { iconTheme: { primary: '#ef4444', secondary: 'white' } },
        }}
      />
      <MainAppContent dictionary={dictionary}>
        {children}
      </MainAppContent>
    </AuthProvider>
  );
}