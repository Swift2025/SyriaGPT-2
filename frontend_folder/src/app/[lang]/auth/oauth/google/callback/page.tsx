// src/app/[lang]/auth/oauth/google/callback/page.tsx
'use client';

import React, { useEffect, useContext } from 'react';
import { useSearchParams, useRouter, useParams } from 'next/navigation';
import { useAuth } from '../../../../../../context/AuthContext';
import toast from 'react-hot-toast';

// دالة API خاصة بهذه الصفحة فقط
const handleGoogleCallback = async (code: string, state: string) => {
  const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL;
  const response = await fetch(`${API_BASE_URL}/auth/oauth/google/callback?code=${code}&state=${state}`);
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.message || 'Google callback failed.');
  }
  return data;
};

export default function GoogleCallbackPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const params = useParams();
  const { login } = useAuth();
  const lang = params.lang as string;

  useEffect(() => {
    const code = searchParams.get('code');
    const state = searchParams.get('state');
    const error = searchParams.get('error');

    if (error) {
      toast.error(`Error from Google: ${error}`);
      router.push(`/${lang}/login`);
      return;
    }

    if (code && state) {
      const processCallback = async () => {
        try {
          const data = await handleGoogleCallback(code, state);
          
          if (typeof window !== 'undefined') {
            localStorage.setItem('accessToken', data.access_token);
          }
          
          login(data.user);
          toast.success(data.message || 'Login successful!');
          router.push(`/${lang}`);

        } catch (err: any) {
          toast.error(err.message);
          router.push(`/${lang}/login`);
        }
      };
      processCallback();
    }
  }, [searchParams, router, login, lang]);

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <div className="w-16 h-16 border-4 border-dashed rounded-full animate-spin border-teal-500"></div>
        <p className="mt-4">Authenticating with Google...</p>
      </div>
    </div>
  );
}