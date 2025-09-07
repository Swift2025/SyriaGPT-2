// src/app/[lang]/auth/oauth/google/callback/page.tsx
'use client';

import React, { useEffect, useState } from 'react';
import { useSearchParams, useRouter, useParams } from 'next/navigation';
import { useAuth } from '../../../../../../context/AuthContext';
import toast from 'react-hot-toast';

// دالة API خاصة بهذه الصفحة فقط
const handleGoogleCallback = async (code: string, state: string, lang: string) => {
  const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:9000';
  const redirect_uri = `${window.location.origin}/${lang}/auth/oauth/google/callback`;
  
  try {
    const response = await fetch(`${API_BASE_URL}/auth/oauth/google/callback?code=${code}&state=${state}&redirect_uri=${encodeURIComponent(redirect_uri)}`);
    
    if (!response.ok) {
      let errorMessage = 'Google callback failed.';
      try {
        const errorData = await response.json();
        errorMessage = errorData.message || errorData.detail || errorMessage;
      } catch (e) {
        errorMessage = `HTTP ${response.status}: ${response.statusText}`;
      }
      throw new Error(errorMessage);
    }
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Google callback error:', error);
    throw error;
  }
};

export default function GoogleCallbackPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const params = useParams();
  const { login } = useAuth();
  const lang = params.lang as string;
  const [isProcessing, setIsProcessing] = useState(false);

  useEffect(() => {
    const code = searchParams.get('code');
    const state = searchParams.get('state');
    const error = searchParams.get('error');

    if (error) {
      toast.error(`Error from Google: ${error}`);
      router.push(`/${lang}/login`);
      return;
    }

    if (code && state && !isProcessing) {
      setIsProcessing(true);
      const processCallback = async () => {
        try {
          const data = await handleGoogleCallback(code, state, lang);
          
          // حفظ الـ token
          if (typeof window !== 'undefined') {
            localStorage.setItem('accessToken', data.access_token);
            localStorage.setItem('userId', data.user_id);
            localStorage.setItem('userEmail', data.email);
            localStorage.setItem('userName', data.full_name);
          }
          
          // إنشاء كائن المستخدم
          const userData = {
            id: data.user_id,
            email: data.email,
            first_name: data.first_name || data.full_name?.split(' ')[0] || '',
            last_name: data.last_name || data.full_name?.split(' ').slice(1).join(' ') || '',
            full_name: data.full_name,
            phone_number: data.phone_number,
            profile_picture: data.profile_picture,
            is_verified: data.is_verified || true,
            is_active: data.is_active || true,
            created_at: new Date(data.created_at || Date.now()),
            updated_at: new Date(data.updated_at || Date.now()),
            last_login: new Date(),
            subscription_tier: data.subscription_tier,
            settings: data.settings
          };
          
          // تسجيل الدخول
          login(userData);
          toast.success(data.message || 'Login successful!');
          
          // الانتقال للصفحة الرئيسية بعد تأخير قصير
          setTimeout(() => {
            router.push(`/${lang}`);
          }, 1000);

        } catch (err: any) {
          console.error('Google callback error:', err);
          let errorMessage = 'Authentication failed';
          
          if (err.message) {
            errorMessage = err.message;
          } else if (err.response?.data?.message) {
            errorMessage = err.response.data.message;
          } else if (err.response?.data?.detail) {
            errorMessage = err.response.data.detail;
          }
          
          // عرض رسالة خطأ أكثر تفصيلاً
          if (errorMessage.includes('OAuth provider') || errorMessage.includes('not configured')) {
            toast.error('Google OAuth غير مُعد بشكل صحيح. يرجى التحقق من الإعدادات.');
          } else if (errorMessage.includes('client_id') || errorMessage.includes('client_secret')) {
            toast.error('مفاتيح Google OAuth غير صحيحة. يرجى التحقق من ملف .env');
          } else {
            toast.error(errorMessage);
          }
          
          router.push(`/${lang}/login`);
        } finally {
          setIsProcessing(false);
        }
      };
      processCallback();
    } else if (!code || !state) {
      router.push(`/${lang}/login`);
    }
  }, [searchParams, router, login, lang, isProcessing]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <div className="w-16 h-16 border-4 border-dashed rounded-full animate-spin border-teal-500 mx-auto"></div>
        <p className="mt-4 text-gray-600 text-lg">جاري المصادقة مع Google...</p>
        <p className="mt-2 text-gray-500 text-sm">يرجى الانتظار...</p>
      </div>
    </div>
  );
}