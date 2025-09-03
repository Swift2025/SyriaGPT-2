// src/app/[lang]/error.tsx
'use client';

import React, { useEffect, useState } from 'react';
import { 
  AlertTriangle, 
  Home, 
  RefreshCw, 
  ArrowLeft, 
  WifiOff,
  HelpCircle,
  Mail,
  Bug,
  ChevronDown,
  Copy,
  CheckCircle,
} from 'lucide-react';
import Link from 'next/link';
import { useRouter, useParams } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { getDictionary } from '../../../get-dictionary'; // استيراد دالة جلب الترجمة
import { Locale } from '../../../i18n-config';

// ==================================
// 1. مكونات فرعية متخصصة (Specialized Subcomponents)
// ==================================

const BackgroundGrid: React.FC = () => (
  <div className="absolute inset-0 -z-10 overflow-hidden">
    <svg className="absolute inset-0 h-full w-full stroke-gray-300/30 dark:stroke-gray-700/30 [mask-image:radial-gradient(100%_100%_at_top_center,white,transparent)]" aria-hidden="true">
      <defs>
        <pattern id="83fd4e5a-9d52-42d3-9d64-3841d61a9721" width="200" height="200" x="50%" y="-1" patternUnits="userSpaceOnUse">
          <path d="M100 200V.5M.5 .5H200" fill="none" />
        </pattern>
      </defs>
      <rect width="100%" height="100%" strokeWidth="0" fill="url(#83fd4e5a-9d52-42d3-9d64-3841d61a9721)" />
    </svg>
  </div>
);

const ActionButton: React.FC<{
  onClick?: () => void;
  href?: string;
  variant?: 'primary' | 'secondary';
  icon: React.ReactNode;
  text: string;
  disabled?: boolean;
}> = ({ onClick, href, variant = 'primary', icon, text, disabled }) => {
  const baseClasses = "w-full flex items-center justify-center gap-2 px-5 py-3 rounded-xl font-semibold transition-all duration-300 transform focus:outline-none focus:ring-4";
  const variantClasses = {
    primary: "bg-gradient-to-r from-teal-500 to-teal-600 text-white hover:from-teal-600 hover:to-teal-700 focus:ring-teal-500/30 disabled:opacity-50",
    secondary: "bg-gray-200/80 dark:bg-gray-700/50 text-gray-800 dark:text-gray-200 hover:bg-gray-300/80 dark:hover:bg-gray-600/50 focus:ring-gray-500/20"
  };

  const content = (
    <motion.button
      whileHover={{ scale: disabled ? 1 : 1.05 }}
      whileTap={{ scale: disabled ? 1 : 0.95 }}
      onClick={onClick}
      disabled={disabled}
      className={`${baseClasses} ${variantClasses[variant]}`}
    >
      {icon}
      {text}
    </motion.button>
  );

  return href ? <Link href={href} passHref legacyBehavior><a>{content}</a></Link> : content;
};

const SuggestionCard: React.FC<{ icon: React.ReactNode; text: string }> = ({ icon, text }) => (
  <div className="flex items-center gap-4 p-4 bg-gray-100/50 dark:bg-gray-800/30 rounded-lg border border-gray-200/50 dark:border-gray-700/50">
    <div className="text-teal-500 dark:text-teal-400 flex-shrink-0">{icon}</div>
    <span className="text-gray-700 dark:text-gray-300">{text}</span>
  </div>
);

const ErrorDetailsAccordion: React.FC<{ statusCode: number; error?: Error & { digest?: string }; dictionary: any }> = ({ statusCode, error, dictionary }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [isCopied, setIsCopied] = useState(false);
  const t = dictionary.errorPage.accordion;

  const copyErrorDetails = () => {
    const errorText = `ErrorCode: ${statusCode}\nMessage: ${error?.message || 'N/A'}\nDigest: ${error?.digest || 'N/A'}\nTimestamp: ${new Date().toISOString()}`;
    navigator.clipboard.writeText(errorText);
    setIsCopied(true);
    setTimeout(() => setIsCopied(false), 2000);
  };

  return (
    <div className="border-t border-gray-200/50 dark:border-gray-700/50 pt-6">
      <button onClick={() => setIsOpen(!isOpen)} className="w-full flex items-center justify-between text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 transition-colors">
        <span className="flex items-center gap-2"><Bug size={16} />{t.title}</span>
        <ChevronDown size={18} className={`transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>
      <AnimatePresence>
        {isOpen && (
          <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }} className="overflow-hidden">
            <div className="mt-4 p-4 bg-gray-100 dark:bg-gray-800 rounded-lg text-xs font-mono text-gray-600 dark:text-gray-400 relative">
              <button onClick={copyErrorDetails} className="absolute top-3 right-3 flex items-center gap-1.5 px-2 py-1 text-xs bg-gray-200 dark:bg-gray-700 rounded-md hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors">
                {isCopied ? <><CheckCircle size={14} className="text-green-500" /> {t.copied}</> : <><Copy size={14} /> {t.copy}</>}
              </button>
              <p><strong>{t.code}</strong> {statusCode}</p>
              {error?.message && <p className="mt-1"><strong>{t.message}</strong> {error.message}</p>}
              {error?.digest && <p className="mt-1"><strong>{t.digest}</strong> {error.digest}</p>}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

// ==================================
// 2. المكون الرئيسي (Main Component)
// ==================================
export default function ErrorPage({ error, reset }: { error: Error & { digest?: string; statusCode?: number }; reset: () => void }) {
  const router = useRouter();
  const params = useParams();
  const [dictionary, setDictionary] = useState<any>(null);
  const [isOnline, setIsOnline] = useState(true);
  const [isRetrying, setIsRetrying] = useState(false);

  const lang = (params.lang || 'ar') as Locale;

  useEffect(() => {
    const fetchDictionary = async () => {
      try {
        const dict = await getDictionary(lang);
        setDictionary(dict);
      } catch (e) {
        console.error("Failed to load dictionary for error page:", e);
      }
    };
    fetchDictionary();
  }, [lang]);

  useEffect(() => {
    const updateOnlineStatus = () => setIsOnline(navigator.onLine);
    window.addEventListener('online', updateOnlineStatus);
    window.addEventListener('offline', updateOnlineStatus);
    return () => {
      window.removeEventListener('online', updateOnlineStatus);
      window.removeEventListener('offline', updateOnlineStatus);
    };
  }, []);

  const handleRetry = async () => {
    setIsRetrying(true);
    await new Promise(resolve => setTimeout(resolve, 1000));
    reset();
  };

  if (!dictionary) {
    return <div className="min-h-screen flex items-center justify-center bg-gray-100 dark:bg-gray-900">Loading...</div>;
  }

  const t = dictionary.errorPage;
  const statusCode = error.statusCode || 500;

  return (
    <main className="min-h-screen bg-gray-100 dark:bg-gray-900 flex items-center justify-center p-4 font-arabic transition-colors duration-500">
      <BackgroundGrid />
      <AnimatePresence>
        {!isOnline && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="fixed top-6 px-4 py-2 bg-red-500 text-white rounded-full flex items-center gap-2 text-sm font-medium shadow-lg z-50"
          >
            <WifiOff size={16} />
            {t.offlineMessage}
          </motion.div>
        )}
      </AnimatePresence>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: "easeOut" }}
        className="relative z-10 w-full max-w-lg bg-white/80 dark:bg-gray-800/80 backdrop-blur-lg rounded-2xl shadow-2xl p-8 md:p-10 border border-black/5 dark:border-white/10"
      >
        <div className="text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-amber-100 dark:bg-amber-900/30 rounded-full mb-6">
            <AlertTriangle className="w-8 h-8 text-amber-500 dark:text-amber-400" />
          </div>
          <p className="font-semibold text-teal-600 dark:text-teal-400 mb-2">{t.errorCode.replace('{statusCode}', statusCode)}</p>
          <h1 className="text-3xl md:text-4xl font-bold text-gray-800 dark:text-white mb-4">{t.title}</h1>
          <p className="text-gray-600 dark:text-gray-400 mb-8 max-w-md mx-auto">{t.description}</p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-8">
          <ActionButton onClick={handleRetry} variant="primary" icon={isRetrying ? <RefreshCw size={18} className="animate-spin" /> : <RefreshCw size={18} />} text={isRetrying ? t.retryingButton : t.retryButton} disabled={isRetrying} />
          <ActionButton href={`/${lang}`} variant="secondary" icon={<Home size={18} />} text={t.homeButton} />
          <ActionButton onClick={() => router.back()} variant="secondary" icon={<ArrowLeft size={18} />} text={t.backButton} />
        </div>

        <div className="space-y-6">
          <div>
            <h3 className="font-semibold text-gray-800 dark:text-gray-200 mb-4 flex items-center gap-2">
              <HelpCircle size={20} className="text-teal-500" />
              {t.suggestionsTitle}
            </h3>
            <div className="space-y-3">
              <SuggestionCard icon={<RefreshCw size={20} />} text={t.suggestion1} />
              {!isOnline && <SuggestionCard icon={<WifiOff size={20} />} text={t.suggestion2} />}
              <SuggestionCard icon={<Mail size={20} />} text={t.suggestion3} />
            </div>
          </div>
          
          <ErrorDetailsAccordion statusCode={statusCode} error={error} dictionary={dictionary} />
        </div>
      </motion.div>
    </main>
  );
}