// src/app/[lang]/forgot-password/ForgotPasswordClient.tsx
'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { Mail, CheckCircle, ArrowRight, Shield, Clock, Key } from 'lucide-react';
import { forgotPassword } from '../../../../services/api'; // استيراد دالة API
import toast from 'react-hot-toast'; // استيراد تنبيهات Toast

// مكون شعار النسر السوري
const SyrianEagle: React.FC<{ className?: string }> = ({ className = "w-16 h-16" }) => (
  <div className={`${className} flex items-center justify-center`}>
    <img src="/images/logo.ai.svg" alt="Syrian Eagle Logo" className="w-full h-full drop-shadow-lg" />
  </div>
);

// مكون الخطوات المرئية
const ProcessStep: React.FC<{ 
  number: number; 
  title: string; 
  description: string; 
  icon: React.ReactNode;
  isActive?: boolean;
}> = ({ number, title, description, icon, isActive = false }) => (
  <div className={`flex items-start gap-4 p-4 rounded-xl transition-all duration-300 ${isActive ? 'bg-gradient-to-r from-amber-50 to-green-50 dark:from-amber-900/20 dark:to-green-900/20 border-2 border-amber-200 dark:border-amber-700' : 'bg-gray-50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700'}`}>
    <div className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center ${isActive ? 'bg-gradient-to-r from-amber-500 to-green-500 text-white shadow-lg' : 'bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-400'}`}>{icon}</div>
    <div className="flex-1">
      <h3 className={`font-semibold mb-1 ${isActive ? 'text-amber-800 dark:text-amber-200' : 'text-gray-700 dark:text-gray-300'}`}>{title}</h3>
      <p className={`text-sm leading-relaxed ${isActive ? 'text-amber-700 dark:text-amber-300' : 'text-gray-600 dark:text-gray-400'}`}>{description}</p>
    </div>
  </div>
);

export default function ForgotPasswordClient({ dictionary }: { dictionary: any }) {
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);

  const params = useParams();
  const lang = params.lang as string;
  const t = dictionary.forgotPasswordPage;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) {
      toast.error(t.form.emailRequiredAlert);
      return;
    }
    setIsLoading(true);
    toast.dismiss();

    try {
      // استدعاء دالة API لإرسال رابط استعادة كلمة المرور
      const data = await forgotPassword(email);
      
      // عرض رسالة النجاح القادمة من الواجهة الخلفية
      toast.success(data.msg);
      setIsSubmitted(true);

    } catch (error: any) {
      toast.error(error.message || 'An unexpected error occurred');
    } finally {
      setIsLoading(false);
    }
  };

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
              <SyrianEagle className="w-24 h-24 mx-auto mb-6" />
              <h2 className="text-3xl font-bold text-gray-800 dark:text-gray-100 mb-4">{t.infoPanel.title}</h2>
              <p className="text-gray-600 dark:text-gray-400 text-lg leading-relaxed max-w-md mx-auto">{t.infoPanel.description}</p>
            </div>
            <div className="space-y-4">
              <ProcessStep number={1} title={t.infoPanel.steps.step1.title} description={t.infoPanel.steps.step1.description} icon={<Mail size={20} />} isActive={!isSubmitted} />
              <ProcessStep number={2} title={t.infoPanel.steps.step2.title} description={t.infoPanel.steps.step2.description} icon={<Shield size={20} />} isActive={isSubmitted} />
              <ProcessStep number={3} title={t.infoPanel.steps.step3.title} description={t.infoPanel.steps.step3.description} icon={<Key size={20} />} />
            </div>
            <div className="mt-8 p-4 bg-amber-100 dark:bg-amber-900/30 rounded-xl border border-amber-200 dark:border-amber-700">
              <div className="flex items-start gap-3">
                <Clock className="text-amber-600 dark:text-amber-400 flex-shrink-0 mt-1" size={20} />
                <div>
                  <h4 className="font-semibold text-amber-800 dark:text-amber-200 mb-1">{t.infoPanel.securityTip.title}</h4>
                  <p className="text-sm text-amber-700 dark:text-amber-300 leading-relaxed">{t.infoPanel.securityTip.description}</p>
                </div>
              </div>
            </div>
          </div>

          <div className="w-full max-w-md mx-auto lg:mx-0">
            <div className="bg-white/90 dark:bg-gray-800/90 backdrop-blur-xl rounded-3xl shadow-2xl p-8 border border-amber-200/50 dark:border-amber-700/30">
              <div className="lg:hidden text-center mb-8">
                <SyrianEagle className="w-20 h-20 mx-auto mb-4" />
                <h1 className="text-3xl font-bold text-gray-800 dark:text-gray-100">{isSubmitted ? t.successScreen.title : t.form.title}</h1>
              </div>
              {isSubmitted ? (
                <div className="text-center animate-fade-in">
                  <div className="w-20 h-20 bg-gradient-to-r from-green-400 to-emerald-500 rounded-full flex items-center justify-center mx-auto mb-6 shadow-lg"><CheckCircle className="text-white" size={40} /></div>
                  <h2 className="text-2xl font-bold text-gray-800 dark:text-gray-100 mb-4">{t.successScreen.checkEmailTitle}</h2>
                  <div className="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-4 mb-6">
                    <p className="text-gray-700 dark:text-gray-300 leading-relaxed">{t.successScreen.description}</p>
                    <p className="font-semibold text-amber-700 dark:text-amber-300 mt-2 break-all">{email}</p>
                  </div>
                  <div className="space-y-4 mb-8">
                    <div className="flex items-center gap-3 p-3 bg-blue-50 dark:bg-blue-900/30 rounded-lg"><div className="w-2 h-2 bg-blue-500 rounded-full flex-shrink-0"></div><p className="text-sm text-blue-800 dark:text-blue-300">{t.successScreen.tip1}</p></div>
                    <div className="flex items-center gap-3 p-3 bg-yellow-50 dark:bg-yellow-900/30 rounded-lg"><div className="w-2 h-2 bg-yellow-500 rounded-full flex-shrink-0"></div><p className="text-sm text-yellow-800 dark:text-yellow-300">{t.successScreen.tip2}</p></div>
                    <div className="flex items-center gap-3 p-3 bg-red-50 dark:bg-red-900/30 rounded-lg"><div className="w-2 h-2 bg-red-500 rounded-full flex-shrink-0"></div><p className="text-sm text-red-800 dark:text-red-300">{t.successScreen.tip3}</p></div>
                  </div>
                  <Link href={`/${lang}/login`}>
                    <button className="w-full flex items-center justify-center gap-2 py-3 px-6 bg-gradient-to-r from-amber-500 to-green-500 hover:from-amber-600 hover:to-green-600 text-white font-semibold rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105 active:scale-95"><ArrowRight size={20} />{t.successScreen.backToLoginButton}</button>
                  </Link>
                </div>
              ) : (
                <div className="animate-fade-in">
                  <div className="lg:hidden text-center mb-6">
                    <h2 className="text-xl font-bold text-gray-800 dark:text-gray-100 mb-2">{t.form.title}</h2>
                    <p className="text-gray-600 dark:text-gray-400">{t.form.description}</p>
                  </div>
                  <form onSubmit={handleSubmit} className="space-y-6">
                    <div>
                      <label htmlFor="email" className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">{t.form.emailLabel}</label>
                      <div className="relative group">
                        <div className="absolute inset-0 bg-gradient-to-r from-amber-400 to-green-400 rounded-xl blur opacity-25 group-hover:opacity-40 transition-opacity duration-300"></div>
                        <div className="relative">
                          <Mail className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 group-hover:text-amber-500 transition-colors duration-300" size={20} />
                          <input id="email" name="email" type="email" autoComplete="email" required value={email} onChange={(e) => setEmail(e.target.value)} className="w-full px-4 py-4 pl-12 bg-white dark:bg-gray-700 border-2 border-gray-200 dark:border-gray-600 rounded-xl text-gray-800 dark:text-gray-200 placeholder-gray-400 focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none transition-all duration-300" placeholder={t.form.emailPlaceholder} />
                        </div>
                      </div>
                    </div>
                    <button type="submit" disabled={isLoading} className="w-full flex items-center justify-center gap-3 py-4 px-6 bg-gradient-to-r from-amber-500 to-green-500 hover:from-amber-600 hover:to-green-600 disabled:from-gray-400 disabled:to-gray-500 text-white font-bold rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105 active:scale-95 disabled:cursor-not-allowed disabled:transform-none group">
                      {isLoading ? (<><div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>{t.form.loadingButton}</>) : (<><Mail className="group-hover:animate-pulse" size={20} />{t.form.submitButton}</>)}
                    </button>
                    <div className="text-center pt-4 border-t border-gray-200 dark:border-gray-600">
                      <p className="text-gray-600 dark:text-gray-400 mb-2">{t.form.rememberedPassword}</p>
                      <Link href={`/${lang}/login`} className="inline-flex items-center gap-2 text-amber-600 dark:text-amber-400 hover:text-amber-700 dark:hover:text-amber-300 font-semibold transition-colors duration-300 group"><ArrowRight className="group-hover:translate-x-1 transition-transform duration-300" size={16} />{t.form.backToLogin}</Link>
                    </div>
                  </form>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
      <style jsx>{`
        @keyframes blob { 0% { transform: translate(0px, 0px) scale(1); } 33% { transform: translate(30px, -50px) scale(1.1); } 66% { transform: translate(-20px, 20px) scale(0.9); } 100% { transform: translate(0px, 0px) scale(1); } }
        @keyframes fade-in { 0% { opacity: 0; transform: translateY(20px); } 100% { opacity: 1; transform: translateY(0); } }
        .animate-blob { animation: blob 7s infinite; }
        .animation-delay-2000 { animation-delay: 2s; }
        .animation-delay-4000 { animation-delay: 4s; }
        .animate-fade-in { animation: fade-in 0.6s ease-out; }
      `}</style>
    </div>
  );
}