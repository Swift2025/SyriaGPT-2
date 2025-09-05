// src/app/[lang]/reset-password/ResetPasswordClient.tsx
'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useParams, useSearchParams } from 'next/navigation';
import { Key, Eye, EyeOff, CheckCircle, XCircle, Lock } from 'lucide-react';
import { AnimatePresence, motion } from 'framer-motion';
import toast from 'react-hot-toast';
import { resetPassword } from '../../../../services/api'; // استيراد دالة API

// ==================================
// 1. مكونات فرعية متخصصة (Specialized Subcomponents)
// ==================================

const PasswordStrengthIndicator: React.FC<{ password?: string; dictionary: any }> = ({ password = '', dictionary }) => {
  const [strength, setStrength] = useState({ score: 0, label: '', color: 'bg-gray-300 dark:bg-gray-700' });
  const t = dictionary.resetPasswordPage.strengthIndicator;

  useEffect(() => {
    let score = 0;
    const checks = [
      password.length >= 8,
      /[A-Z]/.test(password),
      /[a-z]/.test(password),
      /[0-9]/.test(password),
      /[^A-Za-z0-9]/.test(password)
    ];
    
    checks.forEach(check => { if (check) score++; });

    const strengthLevels = [
      { label: t.levels[0], color: 'bg-red-500' },
      { label: t.levels[1], color: 'bg-red-500' },
      { label: t.levels[2], color: 'bg-yellow-500' },
      { label: t.levels[3], color: 'bg-sky-500' },
      { label: t.levels[4], color: 'bg-green-500' },
      { label: t.levels[5], color: 'bg-green-500' }
    ];
    
    setStrength({ score, ...strengthLevels[score] });

  }, [password, t]);

  return (
    <div className="mt-3 space-y-2">
      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5">
        <motion.div 
          className={`h-1.5 rounded-full ${strength.color}`} 
          initial={{ width: 0 }}
          animate={{ width: `${(strength.score / 5) * 100}%` }}
          transition={{ duration: 0.5, ease: "easeInOut" }}
        />
      </div>
      {password.length > 0 && (
        <p className="text-xs font-medium text-gray-500 dark:text-gray-400 text-right">
          {t.title}: {strength.label}
        </p>
      )}
    </div>
  );
};

const PasswordInput: React.FC<{
  id: string;
  label: string;
  value: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  isInvalid?: boolean;
  errorMessage?: string;
  children?: React.ReactNode;
  dictionary: any;
}> = ({ id, label, value, onChange, isInvalid = false, errorMessage, children, dictionary }) => {
  const [showPassword, setShowPassword] = useState(false);
  const t = dictionary.resetPasswordPage.form;

  return (
    <div className="w-full">
      <label htmlFor={id} className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 text-right">
        {label}
      </label>
      <div className="relative">
        <Lock className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 dark:text-gray-500" size={20} />
        <input
          id={id}
          type={showPassword ? 'text' : 'password'}
          required
          value={value}
          onChange={onChange}
          className={`w-full px-4 py-3 pr-11 bg-gray-50 dark:bg-gray-800 border rounded-lg text-gray-900 dark:text-white
                     transition-all duration-300
                     focus:ring-2 focus:ring-offset-2 focus:ring-offset-white dark:focus:ring-offset-gray-900
                     ${isInvalid 
                       ? 'border-red-400 dark:border-red-500 focus:ring-red-500' 
                       : 'border-gray-300 dark:border-gray-600 focus:ring-teal-500'
                     }`}
        />
        <button 
          type="button" 
          onClick={() => setShowPassword(!showPassword)} 
          className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-teal-600 dark:hover:text-teal-400 transition-colors"
          aria-label={showPassword ? t.hidePasswordAria : t.showPasswordAria}
        >
          {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
        </button>
      </div>
      <AnimatePresence>
        {isInvalid && errorMessage && (
          <motion.p 
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="flex items-center gap-1 text-red-600 dark:text-red-500 text-xs mt-2 text-right"
          >
            <XCircle size={14} /> {errorMessage}
          </motion.p>
        )}
      </AnimatePresence>
      {children}
    </div>
  );
};

const SuccessScreen: React.FC<{ dictionary: any }> = ({ dictionary }) => {
  const t = dictionary.resetPasswordPage.successScreen;
  const params = useParams();
  const lang = params.lang as string;

  return (
    <motion.div 
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
      className="w-full max-w-md text-center bg-white dark:bg-gray-800/50 rounded-2xl shadow-2xl p-8 md:p-12 border border-black/5 dark:border-white/10"
    >
      <motion.div
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ type: "spring", stiffness: 260, damping: 20, delay: 0.2 }}
      >
        <CheckCircle className="w-20 h-20 mx-auto text-green-500 mb-6" />
      </motion.div>
      <h1 className="text-3xl font-bold text-gray-800 dark:text-white mb-4">{t.title}</h1>
      <p className="text-gray-600 dark:text-gray-300 mb-8 leading-relaxed">{t.description}</p>
      <Link href={`/${lang}/login`} legacyBehavior>
        <a className="inline-block w-full py-3 px-4 rounded-lg font-semibold text-white bg-teal-600 hover:bg-teal-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-teal-500 transition-transform transform hover:scale-105 active:scale-95">
          {t.backToLoginButton}
        </a>
      </Link>
    </motion.div>
  );
};

// ==================================
// 2. المكون الرئيسي (Main Component)
// ==================================
export default function ResetPasswordClient({ dictionary }: { dictionary: any }) {
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [passwordsDoNotMatch, setPasswordsDoNotMatch] = useState(false);
  
  const searchParams = useSearchParams();
  const t = dictionary.resetPasswordPage;

  useEffect(() => {
    // الحصول على التوكن من رابط URL عند تحميل الصفحة
    const urlToken = searchParams.get('token');
    if (urlToken) {
      setToken(urlToken);
    } else {
      toast.error("Token not found in URL."); // يمكنك ترجمة هذه الرسالة
    }
  }, [searchParams]);

  useEffect(() => {
    setPasswordsDoNotMatch(confirmPassword && password !== confirmPassword);
  }, [password, confirmPassword]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) {
      toast.error("Reset token is missing."); // يمكنك ترجمة هذه
      return;
    }
    if (passwordsDoNotMatch) {
      toast.error(t.form.mismatchToast);
      return;
    }
    
    setIsLoading(true);
    toast.loading(t.form.loadingToast);

    try {
      const data = await resetPassword(token, password, confirmPassword);
      
      toast.dismiss();
      toast.success(data.msg || t.form.successToast);
      setIsSuccess(true);

    } catch (error: any) {
      toast.dismiss();
      toast.error(error.message || 'An unexpected error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  const Background = () => (
    <div className="absolute inset-0 -z-10 overflow-hidden">
      <div className="absolute top-0 -left-4 w-72 h-72 bg-teal-300/20 rounded-full filter blur-3xl opacity-50 animate-blob"></div>
      <div className="absolute top-0 -right-4 w-72 h-72 bg-sky-300/20 rounded-full filter blur-3xl opacity-50 animate-blob animation-delay-2000"></div>
      <div className="absolute bottom-0 left-20 w-72 h-72 bg-indigo-300/20 rounded-full filter blur-3xl opacity-50 animate-blob animation-delay-4000"></div>
    </div>
  );

  return (
    <main className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 p-4 transition-colors duration-500">
      <Background />
      <AnimatePresence mode="wait">
        {isSuccess ? (
          <SuccessScreen key="success" dictionary={dictionary} />
        ) : (
          <motion.div 
            key="form"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.5 }}
            className="w-full max-w-md bg-white/80 dark:bg-gray-800/80 backdrop-blur-lg rounded-2xl shadow-2xl p-8 border border-black/5 dark:border-white/10"
          >
            <div className="text-center mb-8">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-teal-100 dark:bg-teal-900/50 rounded-full mb-4">
                <Key className="w-8 h-8 text-teal-600 dark:text-teal-400" />
              </div>
              <h1 className="text-3xl font-bold text-gray-800 dark:text-white">{t.form.title}</h1>
              <p className="text-gray-600 dark:text-gray-400 mt-2">{t.form.description}</p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
              <PasswordInput
                id="new-password"
                label={t.form.newPasswordLabel}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                dictionary={dictionary}
              >
                <PasswordStrengthIndicator password={password} dictionary={dictionary} />
              </PasswordInput>

              <PasswordInput
                id="confirm-password"
                label={t.form.confirmPasswordLabel}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                isInvalid={passwordsDoNotMatch}
                errorMessage={t.form.passwordMismatchError}
                dictionary={dictionary}
              />

              <div>
                <button 
                  type="submit" 
                  disabled={isLoading || passwordsDoNotMatch || !password || !token} 
                  className="w-full flex justify-center py-3 px-4 rounded-lg font-semibold text-white bg-teal-600 hover:bg-teal-700 
                             transition-all duration-300 transform
                             focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-teal-500
                             hover:scale-105 active:scale-95
                             disabled:bg-gray-400 disabled:dark:bg-gray-600 disabled:cursor-not-allowed disabled:scale-100"
                >
                  {isLoading ? t.form.loadingButton : t.form.submitButton}
                </button>
              </div>
            </form>
          </motion.div>
        )}
      </AnimatePresence>
    </main>
  );
}