// src/app/[lang]/help/HelpPageClient.tsx
'use client';

import React, { useState } from 'react';
import { Search, ChevronDown, LifeBuoy, UserCircle, Lock, Zap, Mail, Sparkles, MessageCircle, Phone, Clock } from 'lucide-react';

// مكون شعار النسر السوري
const SyrianEagle: React.FC<{ className?: string }> = ({ className = "w-16 h-16" }) => (
  <div className={`${className} flex items-center justify-center`}>
    <img src="/images/logo.ai.svg" alt="Syrian Eagle Logo" className="w-full h-full drop-shadow-lg" />
  </div>
);

// المكونات الفرعية المحسنة
const CategoryCard: React.FC<{ 
  icon: React.ReactNode; 
  title: string; 
  description: string;
  gradient: string;
  iconBg: string;
  delay: number;
}> = ({ icon, title, description, gradient, iconBg, delay }) => (
  <div 
    className={`
      relative overflow-hidden group cursor-pointer
      bg-gradient-to-br ${gradient}
      p-6 rounded-2xl border border-amber-200/50 dark:border-amber-700/30
      text-center transition-all duration-500 ease-out
      hover:shadow-2xl hover:scale-105 hover:border-amber-400/70
      transform hover:-rotate-1
      animate-fade-in-up
    `}
    style={{animationDelay: `${delay}ms`}}
  >
    <div className={`absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent 
                    transform -translate-x-full group-hover:translate-x-full 
                    transition-transform duration-1000`}></div>
    <div className={`
      relative w-16 h-16 ${iconBg} rounded-2xl 
      flex items-center justify-center mx-auto mb-6
      shadow-lg group-hover:shadow-xl group-hover:scale-110
      transition-all duration-300
    `}>
      <div className="text-white group-hover:animate-pulse">
        {icon}
      </div>
    </div>
    <h3 className={`text-xl font-bold text-gray-800 dark:text-gray-100 mb-3 
                   group-hover:text-amber-800 dark:group-hover:text-amber-200
                   transition-colors duration-300`}>
      {title}
    </h3>
    <p className={`text-gray-600 dark:text-gray-400 leading-relaxed
                  group-hover:text-gray-700 dark:group-hover:text-gray-300
                  transition-colors duration-300`}>
      {description}
    </p>
    <div className={`absolute bottom-2 right-2 w-3 h-3 bg-amber-400 rounded-full
                    opacity-0 group-hover:opacity-100 group-hover:animate-ping
                    transition-opacity duration-300`}></div>
  </div>
);

const FaqItem: React.FC<{ 
  question: string; 
  children: React.ReactNode;
  index: number;
  dictionary: any;
}> = ({ question, children, index, dictionary }) => {
  const [isOpen, setIsOpen] = useState(false);
  const t = dictionary.helpPage.faq;
  
  return (
    <div className={`
      border-b border-amber-100 dark:border-gray-700 last:border-b-0
      hover:bg-gradient-to-r hover:from-amber-50/50 hover:to-green-50/30
      dark:hover:from-gray-800/30 dark:hover:to-gray-700/30
      transition-all duration-300 rounded-lg
      animate-fade-in-up
    `} style={{animationDelay: `${index * 100}ms`}}>
      <button 
        onClick={() => setIsOpen(!isOpen)} 
        className={`w-full flex justify-between items-center text-right py-6 px-4
                   group focus:outline-none focus:ring-2 focus:ring-amber-400 focus:ring-opacity-50 rounded-lg`}
      >
        <span className={`font-bold text-lg text-gray-800 dark:text-gray-100
                         group-hover:text-amber-800 dark:group-hover:text-amber-200
                         transition-colors duration-300 pr-4`}>
          {question}
        </span>
        <div className="flex items-center gap-3">
          <span className={`text-sm text-amber-600 dark:text-amber-400 font-medium
                          opacity-0 group-hover:opacity-100 transition-opacity duration-300`}>
            {isOpen ? t.toggleClose : t.toggleOpen}
          </span>
          <ChevronDown 
            className={`transform transition-all duration-500 text-amber-600 dark:text-amber-400
                       group-hover:scale-110 ${isOpen ? 'rotate-180' : 'rotate-0'}`} 
            size={24}
          />
        </div>
      </button>
      <div className={`overflow-hidden transition-all duration-500 ease-out ${
        isOpen ? 'max-h-96 opacity-100' : 'max-h-0 opacity-0'
      }`}>
        <div className={`pb-6 px-4 text-gray-700 dark:text-gray-300 leading-relaxed
                        bg-gradient-to-r from-amber-50/30 to-transparent 
                        dark:from-gray-800/20 dark:to-transparent
                        rounded-lg`}>
          <div className="border-r-4 border-amber-300 dark:border-amber-600 pr-4">
            {children}
          </div>
        </div>
      </div>
    </div>
  );
};

// المكون الرئيسي للعميل
export default function HelpPageClient({ dictionary }: { dictionary: any }) {
  const [searchQuery, setSearchQuery] = useState('');
  const t = dictionary.helpPage;

  // تعريف الأجزاء الثابتة (الأيقونات والألوان) للفئات
  const categoryDefinitions = [
    { icon: <LifeBuoy size={24} />, gradient: "from-blue-50 to-indigo-100 dark:from-blue-900/20 dark:to-indigo-900/20", iconBg: "bg-gradient-to-br from-blue-500 to-indigo-600", delay: 0 },
    { icon: <UserCircle size={24} />, gradient: "from-emerald-50 to-green-100 dark:from-emerald-900/20 dark:to-green-900/20", iconBg: "bg-gradient-to-br from-emerald-500 to-green-600", delay: 100 },
    { icon: <Zap size={24} />, gradient: "from-purple-50 to-violet-100 dark:from-purple-900/20 dark:to-violet-900/20", iconBg: "bg-gradient-to-br from-purple-500 to-violet-600", delay: 200 },
    { icon: <Lock size={24} />, gradient: "from-rose-50 to-pink-100 dark:from-rose-900/20 dark:to-pink-900/20", iconBg: "bg-gradient-to-br from-rose-500 to-pink-600", delay: 300 }
  ];

  // دمج التعريفات الثابتة مع النصوص المترجمة من القاموس
  const categories = t.categories.items.map((item: { title: string; description: string }, index: number) => ({
    ...item,
    ...categoryDefinitions[index]
  }));

  return (
    <main className={`flex-1 overflow-y-auto bg-gradient-to-br from-amber-50 via-green-50 to-yellow-50 
                     dark:from-gray-900 dark:via-gray-900 dark:to-gray-800 
                     font-arabic min-h-screen`}>
      
      <div className="fixed inset-0 opacity-30 dark:opacity-10 -z-10">
        <div className={`absolute top-0 left-0 w-72 h-72 bg-amber-300 rounded-full mix-blend-multiply 
                        filter blur-xl opacity-70 animate-blob`}></div>
        <div className={`absolute top-0 right-0 w-72 h-72 bg-green-300 rounded-full mix-blend-multiply 
                        filter blur-xl opacity-70 animate-blob animation-delay-2000`}></div>
        <div className={`absolute bottom-0 left-1/2 w-72 h-72 bg-yellow-300 rounded-full mix-blend-multiply 
                        filter blur-xl opacity-70 animate-blob animation-delay-4000`}></div>
      </div>

      <div className="relative z-10 max-w-6xl mx-auto px-4 py-12 md:py-20">
        
        <header className="text-center mb-16">
          <div className="inline-flex items-center gap-3 mb-6">
            <SyrianEagle className="w-16 h-16 animate-float" />
          </div>
          <h1 className={`text-5xl md:text-6xl font-bold bg-gradient-to-r from-amber-800 via-green-700 to-amber-900 
                         bg-clip-text text-transparent mb-6 animate-fade-in`}>
            {t.header.title}
          </h1>
          <p className="text-xl text-gray-700 dark:text-gray-300 mb-12 max-w-2xl mx-auto leading-relaxed">
            {t.header.description}
          </p>
          <div className="relative max-w-3xl mx-auto group">
            <div className={`absolute inset-0 bg-gradient-to-r from-amber-400 to-green-500 rounded-full blur-lg 
                            opacity-25 group-hover:opacity-40 transition-opacity duration-300`}></div>
            <div className="relative flex items-center">
              <Search className="absolute right-6 text-amber-600 dark:text-amber-400 z-10" size={24} />
              <input 
                type="search" 
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder={t.search.placeholder} 
                className={`w-full pl-6 pr-16 py-4 bg-white/90 dark:bg-gray-800/90 backdrop-blur-sm
                           border-2 border-amber-200 dark:border-amber-700 rounded-full text-lg
                           text-gray-800 dark:text-gray-200 placeholder-gray-500 dark:placeholder-gray-400
                           focus:ring-4 focus:ring-amber-400/30 focus:border-amber-400 
                           focus:bg-white dark:focus:bg-gray-800
                           outline-none transition-all duration-300 shadow-lg
                           hover:shadow-xl hover:border-amber-300`} 
              />
              <button className={`absolute left-2 top-1/2 -translate-y-1/2 w-12 h-12 
                                bg-gradient-to-r from-amber-500 to-green-500 
                                rounded-full flex items-center justify-center
                                text-white hover:from-amber-600 hover:to-green-600
                                transition-all duration-300 shadow-lg hover:shadow-xl
                                hover:scale-105 active:scale-95`}>
                <Search size={20} />
              </button>
            </div>
          </div>
        </header>

        <section className="mb-20">
          <h2 className="text-3xl font-bold text-center mb-12 text-gray-800 dark:text-gray-100">
            {t.categories.title}
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
            {categories.map((category, index) => (
              <CategoryCard key={index} {...category} />
            ))}
          </div>
        </section>

        <section className="mb-20">
          <h2 className="text-4xl font-bold text-center mb-12 text-gray-800 dark:text-gray-100">
            {t.faq.title}
          </h2>
          <div className={`bg-white/60 dark:bg-gray-800/40 backdrop-blur-sm p-8 rounded-3xl 
                          border border-amber-200/50 dark:border-amber-700/30 shadow-2xl`}>
            <div className="space-y-2">
              {t.faq.items.map((faq: { question: string; answer: string }, index: number) => (
                <FaqItem key={index} question={faq.question} index={index} dictionary={dictionary}>
                  <p className="text-base leading-relaxed">{faq.answer}</p>
                </FaqItem>
              ))}
            </div>
          </div>
        </section>

        <section className="text-center">
          <div className={`relative overflow-hidden bg-gradient-to-br from-amber-900 via-green-800 to-amber-900 
                          p-12 rounded-3xl shadow-2xl`}>
            <div className="absolute inset-0 opacity-20">
              <svg width="60" height="60" viewBox="0 0 60 60" xmlns="http://www.w3.org/2000/svg" className="w-full h-full">
                <defs><pattern id="help-dots" x="0" y="0" width="60" height="60" patternUnits="userSpaceOnUse"><circle cx="30" cy="30" r="4" fill="white" fillOpacity="0.1"/></pattern></defs>
                <rect width="100%" height="100%" fill="url(#help-dots)"/>
              </svg>
            </div>
            <div className="relative z-10">
              <div className={`w-20 h-20 bg-white/20 rounded-full flex items-center justify-center mx-auto mb-6
                              shadow-lg backdrop-blur-sm animate-bounce`}>
                <Mail size={40} className="text-white" />
              </div>
              <h2 className="text-4xl font-bold text-white mb-4">{t.contact.title}</h2>
              <p className="text-white/90 text-lg mb-8 max-w-2xl mx-auto leading-relaxed">{t.contact.description}</p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
                <a href="mailto:support@syriagpt.com" className={`inline-flex items-center gap-3 px-8 py-4 bg-white text-amber-700 font-bold rounded-2xl hover:bg-gray-50 hover:scale-105 active:scale-95 transition-all duration-300 shadow-lg hover:shadow-xl group`}>
                  <Mail size={20} className="group-hover:animate-pulse" />{t.contact.emailButton}
                </a>
                <button className={`inline-flex items-center gap-3 px-8 py-4 bg-white/20 text-white font-bold rounded-2xl border-2 border-white/30 hover:bg-white/30 hover:scale-105 active:scale-95 transition-all duration-300 backdrop-blur-sm group`}>
                  <MessageCircle size={20} className="group-hover:animate-bounce" />{t.contact.chatButton}
                </button>
                <a href="tel:+963123456789" className={`inline-flex items-center gap-3 px-8 py-4 bg-white/10 text-white font-bold rounded-2xl border-2 border-white/20 hover:bg-white/20 hover:scale-105 active:scale-95 transition-all duration-300 backdrop-blur-sm group`}>
                  <Phone size={20} className="group-hover:animate-pulse" />{t.contact.phoneButton}
                </a>
              </div>
              <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4 text-white/80 text-sm">
                <div className="flex items-center justify-center gap-2"><Clock size={16} /><span>{t.contact.availability}</span></div>
                <div className="flex items-center justify-center gap-2"><MessageCircle size={16} /><span>{t.contact.responseTime}</span></div>
                <div className="flex items-center justify-center gap-2"><Sparkles size={16} /><span>{t.contact.languageSupport}</span></div>
              </div>
            </div>
          </div>
        </section>

      </div>

      <style jsx>{`
        @keyframes blob { 0% { transform: translate(0px, 0px) scale(1); } 33% { transform: translate(30px, -50px) scale(1.1); } 66% { transform: translate(-20px, 20px) scale(0.9); } 100% { transform: translate(0px, 0px) scale(1); } }
        @keyframes float { 0%, 100% { transform: translateY(0px); } 50% { transform: translateY(-10px); } }
        @keyframes fade-in { 0% { opacity: 0; } 100% { opacity: 1; } }
        @keyframes fade-in-up { 0% { opacity: 0; transform: translateY(20px); } 100% { opacity: 1; transform: translateY(0); } }
        .animate-blob { animation: blob 7s infinite; }
        .animation-delay-2000 { animation-delay: 2s; }
        .animation-delay-4000 { animation-delay: 4s; }
        .animate-float { animation: float 3s ease-in-out infinite; }
        .animate-fade-in { animation: fade-in 1s ease-out; }
        .animate-fade-in-up { animation: fade-in-up 0.8s ease-out forwards; opacity: 0; }
      `}</style>
    </main>
  );
}