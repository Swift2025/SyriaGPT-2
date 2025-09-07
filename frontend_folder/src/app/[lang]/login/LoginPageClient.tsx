// src/app/[lang]/login/LoginPageClient.tsx
'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { Eye, EyeOff, Mail, Lock, ArrowLeft, Shield, Sparkles } from 'lucide-react';
import { loginUser, getGoogleAuthUrl } from '../../../../services/api';
import { useAuth } from '../../../context/AuthContext';
import toast from 'react-hot-toast';

// مكون شعار النسر السوري
const SyrianEagle: React.FC<{ className?: string }> = ({ className = "w-16 h-16" }) => (
  <div className={`${className} flex items-center justify-center`}>
    <img src="/images/logo.ai.svg" alt="Syrian Eagle Logo" className="w-full h-full drop-shadow-lg" />
  </div>
);

// مكون ميزة أمنية
const SecurityFeature: React.FC<{ 
  icon: React.ReactNode;
  title: string;
  description: string;
}> = ({ icon, title, description }) => (
  <div className="flex items-start gap-3 p-4 bg-white/60 dark:bg-gray-800/60 rounded-xl backdrop-blur-sm border border-amber-200/50 dark:border-amber-700/30">
    <div className="flex-shrink-0 w-8 h-8 bg-gradient-to-r from-amber-500 to-green-500 rounded-lg flex items-center justify-center">
      <div className="text-white text-sm">{icon}</div>
    </div>
    <div>
      <h4 className="font-semibold text-gray-800 dark:text-gray-100 text-sm mb-1">{title}</h4>
      <p className="text-xs text-gray-600 dark:text-gray-400 leading-relaxed">{description}</p>
    </div>
  </div>
);

// شاشة تحميل بسيطة
const LoadingScreen = () => (
  <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-amber-50 via-green-50 to-yellow-50 dark:from-gray-900 dark:via-gray-900 dark:to-gray-800" suppressHydrationWarning={true}>
    <div className="w-16 h-16 border-4 border-dashed rounded-full animate-spin border-teal-500" suppressHydrationWarning={true}></div>
  </div>
);

export default function LoginPageClient({ dictionary }: { dictionary: any }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isGoogleLoading, setIsGoogleLoading] = useState(false);

  const router = useRouter();
  const params = useParams();
  const lang = params.lang as string;
  const t = dictionary.loginPage;
  const { user, login, isLoading: isAuthLoading } = useAuth();

  useEffect(() => {
    if (!isAuthLoading && user) {
      router.push(`/${lang}`);
    }
  }, [isAuthLoading, user, router, lang]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    toast.dismiss();

    try {
    const data = await loginUser(email, password);
    
    // api.ts يقوم الآن بحفظ التوكنات تلقائياً، لكن يمكن التأكيد هنا
    if (typeof window !== 'undefined') {
      localStorage.setItem('accessToken', data.access_token);
      if (data.refresh_token) { // تحقق من وجوده
        localStorage.setItem('refreshToken', data.refresh_token);
      }
    }
    
    login(data.user);
    toast.success(data.message || t.form.loginSuccessAlert);
    router.push(`/${lang}`);

    } catch (error: any) {
      toast.error(error.message || 'An unexpected error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleSignIn = async () => {
    setIsGoogleLoading(true);
    try {
      const data = await getGoogleAuthUrl(lang);
      window.location.href = data.authorization_url;
    } catch (error: any) {
      toast.error(error.message || "Failed to start Google Sign-in.");
      setIsGoogleLoading(false);
    }
  };

  if (isAuthLoading || user) {
    return <LoadingScreen />;
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-amber-50 via-green-50 to-yellow-50 dark:from-gray-900 dark:via-gray-900 dark:to-gray-800 p-4">
      
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-amber-300 rounded-full mix-blend-multiply filter blur-xl opacity-30 animate-blob"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-green-300 rounded-full mix-blend-multiply filter blur-xl opacity-30 animate-blob animation-delay-2000"></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-80 h-80 bg-yellow-300 rounded-full mix-blend-multiply filter blur-xl opacity-30 animate-blob animation-delay-4000"></div>
      </div>

      <div className="relative z-10 w-full max-w-6xl mx-auto">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          
          <div className="hidden lg:block">
            <div className="text-center mb-8">
              <SyrianEagle className="w-24 h-24 mx-auto mb-6 animate-float" />
              <h2 className="text-4xl font-bold text-gray-800 dark:text-gray-100 mb-4">{t.infoPanel.title}</h2>
              <p className="text-gray-600 dark:text-gray-400 text-lg leading-relaxed max-w-md mx-auto">{t.infoPanel.description} <span className="font-bold text-amber-700 dark:text-amber-300"> SyriaGPT</span></p>
            </div>
            <div className="space-y-4 mb-8">
              <h3 className="text-xl font-bold text-gray-800 dark:text-gray-100 mb-4 text-center">{t.infoPanel.securityTitle}</h3>
              {t.infoPanel.features.map((feature: { title: string; description: string }, index: number) => (
                <SecurityFeature key={index} icon={[<Shield size={16} />, <Lock size={16} />, <Sparkles size={16} />][index]} title={feature.title} description={feature.description} />
              ))}
            </div>
            <div className="grid grid-cols-3 gap-4 text-center">
              {t.infoPanel.stats.map((stat: { value: string; label: string }, index: number) => (
                <div key={index} className="p-4 bg-white/60 dark:bg-gray-800/60 rounded-xl backdrop-blur-sm">
                  <div className="text-2xl font-bold text-amber-700 dark:text-amber-300">{stat.value}</div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">{stat.label}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="w-full max-w-md mx-auto lg:mx-0">
            <div className="bg-white/90 dark:bg-gray-800/90 backdrop-blur-xl rounded-3xl shadow-2xl p-8 border border-amber-200/50 dark:border-amber-700/30">
              <div className="lg:hidden text-center mb-8">
                <SyrianEagle className="w-20 h-20 mx-auto mb-4" />
                <h1 className="text-3xl font-bold text-gray-800 dark:text-gray-100">{t.form.title}</h1>
                <p className="text-gray-600 dark:text-gray-400 mt-2">{t.infoPanel.title} إلى SyriaGPT</p>
              </div>
              <div className="animate-fade-in">
                <div className="lg:block hidden text-center mb-6">
                  <h2 className="text-2xl font-bold text-gray-800 dark:text-gray-100 mb-2">{t.form.title}</h2>
                  <p className="text-gray-600 dark:text-gray-400">{t.form.description}</p>
                </div>
                <form onSubmit={handleSubmit} className="space-y-6">
                  <div>
                    <label htmlFor="email" className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">{t.form.emailLabel}</label>
                    <div className="relative group">
                      <div className="absolute inset-0 bg-gradient-to-r from-amber-400 to-green-400 rounded-xl blur opacity-25 group-hover:opacity-40 transition-opacity duration-300"></div>
                      <div className="relative">
                        <Mail className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 group-hover:text-amber-500 transition-colors duration-300" size={20} />
                        <input id="email" name="email" type="email" autoComplete="email" required value={email} onChange={(e) => setEmail(e.target.value)} className="w-full px-4 py-4 pr-12 bg-white dark:bg-gray-700 border-2 border-gray-200 dark:border-gray-600 rounded-xl text-gray-800 dark:text-gray-200 placeholder-gray-400 focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none transition-all duration-300" placeholder={t.form.emailPlaceholder} />
                      </div>
                    </div>
                  </div>
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <label htmlFor="password" className="block text-sm font-semibold text-gray-700 dark:text-gray-300">{t.form.passwordLabel}</label>
                      <Link href={`/${lang}/forgot-password`} className="text-sm text-amber-600 dark:text-amber-400 hover:text-amber-700 dark:hover:text-amber-300 font-medium transition-colors duration-300">{t.form.forgotPassword}</Link>
                    </div>
                    <div className="relative group">
                      <div className="absolute inset-0 bg-gradient-to-r from-amber-400 to-green-400 rounded-xl blur opacity-25 group-hover:opacity-40 transition-opacity duration-300"></div>
                      <div className="relative">
                        <Lock className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 group-hover:text-amber-500 transition-colors duration-300" size={20} />
                        <input id="password" name="password" type={showPassword ? 'text' : 'password'} autoComplete="current-password" required value={password} onChange={(e) => setPassword(e.target.value)} className="w-full px-4 py-4 pr-12 pl-12 bg-white dark:bg-gray-700 border-2 border-gray-200 dark:border-gray-600 rounded-xl text-gray-800 dark:text-gray-200 placeholder-gray-400 focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none transition-all duration-300" placeholder={t.form.passwordPlaceholder} />
                        <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-amber-500 transition-colors duration-300 p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600" aria-label={showPassword ? t.form.hidePassword : t.form.showPassword}>{showPassword ? <EyeOff size={20} /> : <Eye size={20} />}</button>
                      </div>
                    </div>
                  </div>
                  <button type="submit" disabled={isLoading || !email || !password} className="w-full flex items-center justify-center gap-3 py-4 px-6 bg-gradient-to-r from-amber-500 to-green-500 hover:from-amber-600 hover:to-green-600 disabled:from-gray-400 disabled:to-gray-500 text-white font-bold rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105 active:scale-95 disabled:cursor-not-allowed disabled:transform-none group">
                    {isLoading ? (<><div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>{t.form.loadingButton}</>) : (<><ArrowLeft className="group-hover:translate-x-1 transition-transform duration-300" size={20} />{t.form.loginButton}</>)}
                  </button>
                  <div className="relative"><div className="absolute inset-0 flex items-center"><div className="w-full border-t border-gray-300 dark:border-gray-600"></div></div><div className="relative flex justify-center text-sm"><span className="px-4 bg-white dark:bg-gray-800 text-gray-500 dark:text-gray-400">{t.form.orSeparator}</span></div></div>
                  <button type="button" onClick={handleGoogleSignIn} disabled={isLoading || isGoogleLoading} className="w-full flex items-center justify-center gap-3 px-4 py-4 border-2 border-gray-200 dark:border-gray-600 rounded-xl bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 transition-all duration-300 hover:border-gray-300 dark:hover:border-gray-500 disabled:opacity-50">
                    {isGoogleLoading ? (<div className="w-5 h-5 border-2 border-gray-400 border-t-transparent rounded-full animate-spin"></div>) : (<svg viewBox="0 0 24 24" width="20" height="20"><path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/><path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/><path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/><path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/></svg>)}
                    {t.form.googleButton || "تسجيل الدخول بـ Google"}
                  </button>
                  <div className="text-center space-y-4">
                    <p className="text-gray-600 dark:text-gray-400">{t.form.noAccount}</p>
                    <Link href={`/${lang}/register`} className="inline-flex items-center gap-2 text-amber-600 dark:text-amber-400 hover:text-amber-700 dark:hover:text-amber-300 font-semibold transition-colors duration-300 group"><ArrowLeft className="group-hover:translate-x-1 transition-transform duration-300" size={16} />{t.form.createAccount}</Link>
                  </div>
                </form>
              </div>
            </div>
          </div>
        </div>
      </div>
      <style jsx>{`
        @keyframes blob { 0% { transform: translate(0px, 0px) scale(1); } 33% { transform: translate(30px, -50px) scale(1.1); } 66% { transform: translate(-20px, 20px) scale(0.9); } 100% { transform: translate(0px, 0px) scale(1); } }
        @keyframes float { 0%, 100% { transform: translateY(0px); } 50% { transform: translateY(-10px); } }
        @keyframes fade-in { 0% { opacity: 0; transform: translateY(20px); } 100% { opacity: 1; transform: translateY(0); } }
        .animate-blob { animation: blob 7s infinite; }
        .animation-delay-2000 { animation-delay: 2s; }
        .animation-delay-4000 { animation-delay: 4s; }
        .animate-float { animation: float 3s ease-in-out infinite; }
        .animate-fade-in { animation: fade-in 0.6s ease-out; }
      `}</style>
    </div>
  );
}