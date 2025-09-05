// src/app/[lang]/register/RegisterPageClient.tsx
'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { Eye, EyeOff, User, Mail, Lock, CheckCircle, AlertCircle, ArrowLeft, Shield, Sparkles, Users, Zap } from 'lucide-react';
import { registerUser } from '../../../../services/api';
import { useAuth } from '../../../context/AuthContext';
import toast from 'react-hot-toast';

// مكون شعار النسر السوري
const SyrianEagle: React.FC<{ className?: string }> = ({ className = "w-16 h-16" }) => (
  <div className={`${className} flex items-center justify-center`}>
    <img src="/images/logo.ai.svg" alt="Syrian Eagle Logo" className="w-full h-full drop-shadow-lg" />
  </div>
);

// مكون حقل الإدخال المحسن
const InputField: React.FC<{
  id: string;
  name: string;
  type: string;
  label: string;
  value: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  error?: string;
  required?: boolean;
  autoComplete?: string;
  icon?: React.ReactNode;
  showPasswordToggle?: boolean;
  onTogglePassword?: () => void;
  isPasswordVisible?: boolean;
  placeholder?: string;
}> = ({ 
  id, name, type, label, value, onChange, error, required, autoComplete, 
  icon, showPasswordToggle, onTogglePassword, isPasswordVisible, placeholder
}) => {
  const inputType = showPasswordToggle ? (isPasswordVisible ? 'text' : 'password') : type;
  
  return (
    <div className="space-y-3">
      <label htmlFor={id} className="flex items-center text-sm font-semibold text-gray-700 dark:text-gray-300">
        {icon && <span className="ml-2 text-amber-600 dark:text-amber-400">{icon}</span>}
        {label}
        {required && <span className="text-red-500 mr-1">*</span>}
      </label>
      
      <div className="relative group">
        <div className="absolute inset-0 bg-gradient-to-r from-amber-400 to-green-400 rounded-xl blur opacity-25 group-hover:opacity-40 transition-opacity duration-300"></div>
        <div className="relative">
          <input
            id={id}
            name={name}
            type={inputType}
            required={required}
            value={value}
            onChange={onChange}
            autoComplete={autoComplete}
            className={`
              w-full px-4 py-4 rounded-xl border-2 transition-all duration-300
              bg-white dark:bg-gray-700 backdrop-blur-sm
              text-gray-800 dark:text-gray-200
              placeholder-gray-400
              focus:outline-none focus:ring-2 focus:ring-amber-500
              ${error 
                ? 'border-red-400 focus:border-red-500' 
                : 'border-gray-200 dark:border-gray-600 focus:border-amber-500 hover:border-gray-300 dark:hover:border-gray-500'
              }
              ${showPasswordToggle ? 'pl-12' : ''}
            `}
            placeholder={placeholder || `أدخل ${label}...`}
            dir="auto"
          />
          
          {showPasswordToggle && (
            <button
              type="button"
              onClick={onTogglePassword}
              className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-amber-500 transition-colors duration-300 p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600"
            >
              {isPasswordVisible ? <EyeOff size={20} /> : <Eye size={20} />}
            </button>
          )}
        </div>
      </div>
      
      {error && (
        <div className="flex items-center gap-2 text-red-500 text-sm animate-fade-in">
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
};

// مكون مؤشر قوة كلمة المرور
const PasswordStrengthIndicator: React.FC<{ password: string; dictionary: any }> = ({ password, dictionary }) => {
  const t = dictionary.registerPage.form;
  const getStrength = (password: string) => {
    let score = 0;
    if (password.length >= 8) score++;
    if (/[a-z]/.test(password)) score++;
    if (/[A-Z]/.test(password)) score++;
    if (/\d/.test(password)) score++;
    if (/[^a-zA-Z\d]/.test(password)) score++;
    return score;
  };

  const strength = getStrength(password);
  const strengthLabels = t.strengthLevels;
  const strengthColors = ['bg-red-500', 'bg-orange-500', 'bg-yellow-500', 'bg-green-500', 'bg-emerald-500'];

  if (!password) return null;

  return (
    <div className="mt-3 space-y-2">
      <div className="flex gap-1">
        {[1, 2, 3, 4, 5].map((level) => (
          <div
            key={level}
            className={`h-2 flex-1 rounded-full transition-all duration-300 ${
              level <= strength ? strengthColors[strength - 1] : 'bg-gray-200 dark:bg-gray-600'
            }`}
          />
        ))}
      </div>
      <p className="text-xs text-gray-600 dark:text-gray-400">
        {t.passwordStrength}: <span className={`font-semibold ${strength >= 4 ? 'text-green-600' : strength >= 3 ? 'text-yellow-600' : 'text-red-600'}`}>
          {strengthLabels[strength - 1] || strengthLabels[0]}
        </span>
      </p>
    </div>
  );
};

// مكون ميزة المنصة
const PlatformFeature: React.FC<{
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
  <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-amber-50 via-green-50 to-yellow-50 dark:from-gray-900 dark:via-gray-900 dark:to-gray-800">
    <div className="w-16 h-16 border-4 border-dashed rounded-full animate-spin border-teal-500"></div>
  </div>
);

export default function RegisterPageClient({ dictionary }: { dictionary: any }) {
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    password: '',
    confirmPassword: ''
  });
  
  const [errors, setErrors] = useState<{ [key: string]: string }>({});
  const [isLoading, setIsLoading] = useState(false);
  const [isGoogleLoading, setIsGoogleLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const router = useRouter();
  const params = useParams();
  const lang = params.lang as string;
  const t = dictionary.registerPage;
  const v = t.validation;
  const { user, isLoading: isAuthLoading } = useAuth();

  useEffect(() => {
    if (!isAuthLoading && user) {
      router.push(`/${lang}`);
    }
  }, [isAuthLoading, user, router, lang]);

  const validateField = (name: string, value: string, confirmPassword?: string) => {
    switch (name) {
      case 'first_name':
      case 'last_name':
        if (value.length < 2) return v.minLength;
        if (value.length > 50) return v.maxLength;
        return '';
      case 'email':
        if (!value) return v.emailRequired;
        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) return v.emailInvalid;
        return '';
      case 'password':
        if (value.length < 8) return v.passwordLength;
        if (!/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(value)) return v.passwordComplexity;
        return '';
      case 'confirmPassword':
        if (value !== confirmPassword) return v.passwordMismatch;
        return '';
      default:
        return '';
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    const error = validateField(name, value, name === 'confirmPassword' ? formData.password : undefined);
    setErrors(prev => ({ ...prev, [name]: error }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    toast.dismiss();
// لبتحقق من جنب العميل
    const newErrors: { [key: string]: string } = {};
    Object.keys(formData).forEach(key => {
      const error = validateField(key, formData[key as keyof typeof formData], formData.password);
      if (error) newErrors[key] = error;
    });
    
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      setIsLoading(false);
      return;
    }

    try {
      const userData = {
        email: formData.email,
        password: formData.password,
        password2: formData.confirmPassword,
        first_name: formData.first_name,
        last_name: formData.last_name,
      };

      const data = await registerUser(userData);
      
      toast.success(data.message || t.form.successAlert || "Account created successfully! Please log in.");

      setTimeout(() => {
        router.push(`/${lang}/login`);
      }, 2000);

    } catch (error: any) {
      toast.error(error.message || 'An unexpected error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  // const handleGoogleSignIn = async () => {
  //   setIsGoogleLoading(true);
  //   try {
  //     const data = await getGoogleAuthUrl();
  //     window.location.href = data.authorization_url;
  //   } catch (error: any) {
  //     toast.error(error.message || "Failed to start Google Sign-in.");
  //     setIsGoogleLoading(false);
  //   }
  // };

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

      <div className="relative z-10 w-full max-w-7xl mx-auto">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          
          <div className="hidden lg:block">
            <div className="text-center mb-8">
              <SyrianEagle className="w-24 h-24 mx-auto mb-6 animate-float" />
              <h2 className="text-4xl font-bold text-gray-800 dark:text-gray-100 mb-4">{t.infoPanel.title}</h2>
              <p className="text-gray-600 dark:text-gray-400 text-lg leading-relaxed max-w-md mx-auto">{t.infoPanel.description}</p>
            </div>
            <div className="space-y-4 mb-8">
              {t.infoPanel.features.map((feature: { title: string; description: string }, index: number) => (
                <PlatformFeature key={index} icon={[<Sparkles size={16}/>, <Shield size={16}/>, <Users size={16}/>, <Zap size={16}/>][index]} title={feature.title} description={feature.description} />
              ))}
            </div>
            <div className="bg-white/60 dark:bg-gray-800/60 rounded-xl p-6 backdrop-blur-sm border border-amber-200/50 dark:border-amber-700/30">
              <div className="text-center">
                <div className="flex justify-center mb-3">{[1,2,3,4,5].map((star) => <div key={star} className="text-yellow-400 text-lg">★</div>)}</div>
                <p className="text-gray-700 dark:text-gray-300 text-sm italic mb-3">{t.infoPanel.testimonial.quote}</p>
                <p className="text-xs text-gray-500 dark:text-gray-400">{t.infoPanel.testimonial.author}</p>
              </div>
            </div>
          </div>

          <div className="w-full max-w-md mx-auto lg:mx-0">
            <div className="bg-white/90 dark:bg-gray-800/90 backdrop-blur-xl rounded-3xl shadow-2xl p-8 border border-amber-200/50 dark:border-amber-700/30">
              <div className="lg:hidden text-center mb-8">
                <SyrianEagle className="w-20 h-20 mx-auto mb-4" />
                <h1 className="text-3xl font-bold text-gray-800 dark:text-gray-100">{t.form.title}</h1>
                <p className="text-gray-600 dark:text-gray-400 mt-2">{t.infoPanel.title}</p>
              </div>
              <div className="animate-fade-in">
                <div className="lg:block hidden text-center mb-6">
                  <h2 className="text-2xl font-bold text-gray-800 dark:text-gray-100 mb-2">{t.form.title}</h2>
                  <p className="text-gray-600 dark:text-gray-400">{t.form.description}</p>
                </div>
                <form onSubmit={handleSubmit} className="space-y-6">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <InputField id="first_name" name="first_name" type="text" label={t.form.firstName} value={formData.first_name} onChange={handleChange} error={errors.first_name} required autoComplete="given-name" icon={<User size={16} />} />
                    <InputField id="last_name" name="last_name" type="text" label={t.form.lastName} value={formData.last_name} onChange={handleChange} error={errors.last_name} required autoComplete="family-name" icon={<User size={16} />} />
                  </div>
                  <InputField id="email" name="email" type="email" label={t.form.email} value={formData.email} onChange={handleChange} error={errors.email} required autoComplete="email" icon={<Mail size={16} />} placeholder={t.form.emailPlaceholder} />
                  <div>
                    <InputField id="password" name="password" type="password" label={t.form.password} value={formData.password} onChange={handleChange} error={errors.password} required autoComplete="new-password" icon={<Lock size={16} />} showPasswordToggle onTogglePassword={() => setShowPassword(!showPassword)} isPasswordVisible={showPassword} />
                    <PasswordStrengthIndicator password={formData.password} dictionary={dictionary} />
                  </div>
                  <InputField id="confirmPassword" name="confirmPassword" type="password" label={t.form.confirmPassword} value={formData.confirmPassword} onChange={handleChange} error={errors.confirmPassword} required autoComplete="new-password" icon={<Lock size={16} />} showPasswordToggle onTogglePassword={() => setShowConfirmPassword(!showConfirmPassword)} isPasswordVisible={showConfirmPassword} />
                  <button type="submit" disabled={isLoading || Object.values(errors).some(e => e !== '')} className="w-full flex items-center justify-center gap-3 py-4 px-6 bg-gradient-to-r from-amber-500 to-green-500 hover:from-amber-600 hover:to-green-600 disabled:from-gray-400 disabled:to-gray-500 text-white font-bold rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105 active:scale-95 disabled:cursor-not-allowed disabled:transform-none group">
                    {isLoading ? (<><div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>{t.form.loadingButton}</>) : (<><CheckCircle className="group-hover:animate-pulse" size={20} />{t.form.submitButton}</>)}
                  </button>
                  <div className="relative"><div className="absolute inset-0 flex items-center"><div className="w-full border-t border-gray-300 dark:border-gray-600"></div></div><div className="relative flex justify-center text-sm"><span className="px-4 bg-white dark:bg-gray-800 text-gray-500 dark:text-gray-400">{t.form.orSeparator}</span></div></div>
                  {/* <button type="button" onClick={handleGoogleSignIn} disabled={isLoading || isGoogleLoading} className="w-full flex items-center justify-center gap-3 px-4 py-4 border-2 border-gray-200 dark:border-gray-600 rounded-xl bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 transition-all duration-300 hover:border-gray-300 dark:hover:border-gray-500 disabled:opacity-50">
                    {isGoogleLoading ? (<div className="w-5 h-5 border-2 border-gray-400 border-t-transparent rounded-full animate-spin"></div>) : (<svg viewBox="0 0 24 24" width="20" height="20"><path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/><path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/><path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/><path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/></svg>)}
                    {t.form.googleButton}
                  </button> */}
                  <div className="text-center pt-4 border-t border-gray-200 dark:border-gray-600">
                    <p className="text-gray-600 dark:text-gray-400 mb-2">{t.form.hasAccount}</p>
                    <Link href={`/${lang}/login`} className="inline-flex items-center gap-2 text-amber-600 dark:text-amber-400 hover:text-amber-700 dark:hover:text-amber-300 font-semibold transition-colors duration-300 group"><ArrowLeft className="group-hover:translate-x-1 transition-transform duration-300" size={16} />{t.form.loginLink}</Link>
                  </div>
                  <div className="text-center text-xs text-gray-500 dark:text-gray-400 leading-relaxed">
                    <p>{t.form.termsAgreement} <Link href={`/${lang}/terms`} className="text-amber-600 dark:text-amber-400 hover:underline font-medium">{t.form.termsLink}</Link> {t.form.and} <Link href={`/${lang}/privacy`} className="text-amber-600 dark:text-amber-400 hover:underline font-medium">{t.form.privacyLink}</Link></p>
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