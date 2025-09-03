// src/app/[lang]/verify-email/VerifyEmailClient.tsx
'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams, useParams } from 'next/navigation';
import { CheckCircle, XCircle, RefreshCw, ArrowLeft, Shield } from 'lucide-react';
import { verifyEmail } from '../../../../services/api'; // استيراد دالة API
import toast from 'react-hot-toast';

// مكون النسر السوري
const SyrianEagle: React.FC<{ className?: string }> = ({ className = "w-16 h-16" }) => (
  <div className={`${className} flex items-center justify-center rounded-full bg-brand-cream dark:bg-brand-navy-dark p-1`}>
    <img src="/images/logo.ai.svg" alt="Syrian Eagle Logo" className="w-full h-full" />
  </div>
);

export default function VerifyEmailClient({ dictionary }: { dictionary: any }) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const params = useParams();
  const lang = params.lang as string;
  
  const [status, setStatus] = useState<'verifying' | 'success' | 'error'>('verifying');
  const [errorMessage, setErrorMessage] = useState('');
  
  const t = dictionary.verifyEmailPage;

  useEffect(() => {
    const token = searchParams.get('token');

    if (!token) {
      setStatus('error');
      setErrorMessage('Verification token is missing.'); // يمكنك ترجمة هذه
      return;
    }

    const handleVerification = async () => {
      try {
        const data = await verifyEmail(token);
        setStatus('success');
        toast.success(data.message);
        
        // توجيه المستخدم إلى صفحة تسجيل الدخول بعد 3 ثوانٍ
        setTimeout(() => {
          router.push(`/${lang}/login`);
        }, 3000);

      } catch (error: any) {
        setStatus('error');
        setErrorMessage(error.message || t.errors.generic);
        toast.error(error.message || t.errors.generic);
      }
    };

    handleVerification();
  }, [searchParams, lang, router, t.errors.generic]);

  const StatusDisplay = () => {
    switch (status) {
      case 'verifying':
        return (
          <div className="text-center py-8">
            <div className="w-20 h-20 bg-blue-100 dark:bg-blue-900/20 rounded-full flex items-center justify-center mx-auto mb-4">
              <RefreshCw className="w-12 h-12 text-blue-500 animate-spin" />
            </div>
            <h3 className="text-xl font-bold text-gray-800 dark:text-white mb-2">{t.form.verifyingButton}</h3>
            <p className="text-gray-600 dark:text-gray-400">{t.header.description}...</p>
          </div>
        );
      case 'success':
        return (
          <div className="text-center py-8">
            <div className="w-20 h-20 bg-green-100 dark:bg-green-900/20 rounded-full flex items-center justify-center mx-auto mb-4 animate-bounce-slow">
              <CheckCircle className="w-12 h-12 text-green-500" />
            </div>
            <h3 className="text-xl font-bold text-gray-800 dark:text-white mb-2">{t.status.success.title}</h3>
            <p className="text-gray-600 dark:text-gray-400 mb-4">{t.status.success.description}</p>
            <div className="flex items-center justify-center gap-2 text-[#428177] dark:text-[#B9A779]">
              <RefreshCw className="w-4 h-4 animate-spin" /><span className="text-sm">{t.status.success.redirecting}</span>
            </div>
          </div>
        );
      case 'error':
        return (
          <div className="text-center py-8">
            <div className="w-20 h-20 bg-red-100 dark:bg-red-900/20 rounded-full flex items-center justify-center mx-auto mb-4">
              <XCircle className="w-12 h-12 text-red-500" />
            </div>
            <h3 className="text-xl font-bold text-gray-800 dark:text-white mb-2">{t.status.error.title}</h3>
            <p className="text-gray-600 dark:text-gray-400 mb-6">{errorMessage}</p>
            <Link href={`/${lang}/login`} className="px-6 py-2 bg-[#428177] text-white rounded-lg hover:bg-[#054239] transition-colors">
              {t.backToLogin}
            </Link>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#D9D9D9] to-gray-200 dark:from-[#002326] dark:to-[#054239] flex items-center justify-center px-4 py-12">
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-[#428177]/10 rounded-full blur-3xl"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-[#B9A779]/10 rounded-full blur-3xl"></div>
      </div>

      <div className="relative z-10 w-full max-w-md">
        <div className="text-center mb-8">
          <Link href={`/${lang}`} className="inline-block"><SyrianEagle className="w-20 h-20 mx-auto mb-4" /></Link>
          <h1 className="text-3xl font-bold text-[#054239] dark:text-[#B9A779] mb-2">{t.header.title}</h1>
        </div>

        <div className="bg-white/90 dark:bg-[#161616]/90 backdrop-blur-lg rounded-2xl shadow-xl p-8">
          <StatusDisplay />
        </div>
      </div>
      <style jsx>{`
        @keyframes bounce-slow { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-10px); } }
        .animate-bounce-slow { animation: bounce-slow 2s ease-in-out infinite; }
      `}</style>
    </div>
  );
};