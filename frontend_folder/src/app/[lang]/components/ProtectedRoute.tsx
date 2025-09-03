// src/components/ProtectedRoute.tsx
'use client';

import React, { useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { useAuth } from '../../../context/AuthContext';

// شاشة تحميل بسيطة
const LoadingScreen = () => (
  <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 via-white to-gray-100 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
    <div className="w-16 h-16 border-4 border-dashed rounded-full animate-spin border-teal-500"></div>
  </div>
);

const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { user, isLoading } = useAuth();
  const router = useRouter();
  const params = useParams();
  const lang = params.lang as string;

  useEffect(() => {
    // إذا انتهى التحميل ولم يكن هناك مستخدم، قم بالتوجيه إلى صفحة تسجيل الدخول
    if (!isLoading && !user) {
      router.push(`/${lang}/login`);
    }
  }, [isLoading, user, router, lang]);

  // أثناء التحقق من حالة المستخدم، اعرض شاشة تحميل
  if (isLoading) {
    return <LoadingScreen />;
  }

  // إذا كان المستخدم موجوداً، اعرض المحتوى المحمي (الصفحة)
  if (user) {
    return <>{children}</>;
  }

  // إذا لم يكن المستخدم موجوداً (قبل أن يعمل التوجيه)، لا تعرض شيئاً
  return null;
};

export default ProtectedRoute;