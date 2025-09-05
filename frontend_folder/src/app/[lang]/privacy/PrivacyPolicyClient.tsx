// src/app/[lang]/privacy/PrivacyPolicyClient.tsx
'use client';

import React, { useState } from 'react';
import { ShieldCheck, Lock, Eye, FileText, Users, Bell, Phone, Mail, ArrowUp, Check } from 'lucide-react';

// مكون شعار النسر السوري
const SyrianEagle: React.FC<{ className?: string }> = ({ className = "w-16 h-16" }) => (
  <div className={`${className} flex items-center justify-center`}>
    <img src="/images/logo.ai.svg" alt="Syrian Eagle Logo" className="w-full h-full drop-shadow-lg" />
  </div>
);

// مكون قسم معلومات
const InfoSection: React.FC<{
  icon: React.ReactNode;
  title: string;
  description: string;
  bgColor: string;
}> = ({ icon, title, description, bgColor }) => (
  <div className={`p-6 rounded-2xl ${bgColor} border border-amber-200/50 dark:border-amber-700/30 transition-all duration-300 hover:scale-105 hover:shadow-lg`}>
    <div className="flex items-start gap-4">
      <div className="flex-shrink-0 w-12 h-12 bg-gradient-to-br from-amber-500 to-green-500 rounded-xl flex items-center justify-center shadow-lg">
        <div className="text-white">
          {icon}
        </div>
      </div>
      <div>
        <h3 className="font-bold text-lg text-gray-800 dark:text-gray-100 mb-2">{title}</h3>
        <p className="text-gray-600 dark:text-gray-400 leading-relaxed">{description}</p>
      </div>
    </div>
  </div>
);

// مكون القائمة التفاعلية
const InteractiveList: React.FC<{
  items: string[];
  type: 'bullets' | 'checks';
}> = ({ items, type }) => (
  <ul className="space-y-3 my-6">
    {items.map((item, index) => (
      <li key={index} className="flex items-start gap-3 p-3 bg-amber-50/50 dark:bg-gray-800/50 rounded-lg border border-amber-200/30 dark:border-amber-700/30">
        <div className="flex-shrink-0 w-6 h-6 rounded-full bg-gradient-to-r from-amber-500 to-green-500 flex items-center justify-center mt-0.5">
          {type === 'checks' ? (
            <Check size={14} className="text-white" />
          ) : (
            <div className="w-2 h-2 bg-white rounded-full"></div>
          )}
        </div>
        <span className="text-gray-700 dark:text-gray-300 leading-relaxed">{item}</span>
      </li>
    ))}
  </ul>
);

// مكون جدول المحتويات
const TableOfContents: React.FC<{
  sections: { id: string; title: string }[];
  activeSection: string;
  onSectionClick: (id: string) => void;
  dictionary: any;
}> = ({ sections, activeSection, onSectionClick, dictionary }) => (
  <div className="sticky top-8 bg-white/90 dark:bg-gray-800/90 backdrop-blur-xl rounded-2xl p-6 border border-amber-200/50 dark:border-amber-700/30 shadow-lg">
    <h3 className="font-bold text-lg text-gray-800 dark:text-gray-100 mb-4 flex items-center gap-2">
      <FileText size={20} className="text-amber-600" />
      {dictionary.privacyPolicyPage.toc.title}
    </h3>
    <nav className="space-y-2">
      {sections.map((section, index) => (
        <button
          key={section.id}
          onClick={() => onSectionClick(section.id)}
          className={`w-full text-right p-3 rounded-lg transition-all duration-300 ${
            activeSection === section.id
              ? 'bg-gradient-to-r from-amber-500 to-green-500 text-white shadow-lg'
              : 'text-gray-600 dark:text-gray-400 hover:bg-amber-50 dark:hover:bg-gray-700 hover:text-amber-700 dark:hover:text-amber-300'
          }`}
        >
          <span className="text-sm font-medium">{index + 1}. {section.title}</span>
        </button>
      ))}
    </nav>
  </div>
);

export default function PrivacyPolicyClient({ dictionary }: { dictionary: any }) {
  const [activeSection, setActiveSection] = useState('introduction');
  const t = dictionary.privacyPolicyPage;

  const sections = t.sections.map((section: { id: string; title: string }) => ({
    id: section.id,
    title: section.title
  }));

  const handleSectionClick = (sectionId: string) => {
    setActiveSection(sectionId);
    const element = document.getElementById(sectionId);
    if (element) {
      // استخدام scrollIntoView مع تعديل بسيط لضمان عدم تغطية العنوان
      const elementPosition = element.getBoundingClientRect().top;
      const offsetPosition = elementPosition + window.pageYOffset - 80; // 80px offset
    
      window.scrollTo({
         top: offsetPosition,
         behavior: "smooth"
      });
    }
  };

  return (
    <main className="flex-1 overflow-y-auto bg-gradient-to-br from-amber-50 via-green-50 to-yellow-50 dark:from-gray-900 dark:via-gray-900 dark:to-gray-800 font-arabic min-h-screen">
      
      <div className="fixed inset-0 opacity-30 dark:opacity-10 -z-10">
        <div className="absolute top-0 left-0 w-72 h-72 bg-amber-300 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-blob"></div>
        <div className="absolute top-0 right-0 w-72 h-72 bg-green-300 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-blob animation-delay-2000"></div>
        <div className="absolute bottom-0 left-1/2 w-72 h-72 bg-yellow-300 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-blob animation-delay-4000"></div>
      </div>

      <div className="relative z-10 max-w-7xl mx-auto px-4 py-12 md:py-20">
        
        <header className="text-center mb-16">
          <div className="inline-flex items-center gap-3 mb-6">
            <SyrianEagle className="w-16 h-16 animate-float" />
          </div>
          <h1 className="text-5xl md:text-6xl font-bold bg-gradient-to-r from-amber-800 via-green-700 to-amber-900 bg-clip-text text-transparent mb-6">
            {t.header.title}
          </h1>
          <div className="flex items-center justify-center gap-4 text-gray-600 dark:text-gray-400">
            <div className="flex items-center gap-2"><Bell size={16} /><span>{t.header.lastUpdated}</span></div>
            <div className="w-1 h-1 bg-gray-400 rounded-full"></div>
            <div className="flex items-center gap-2"><Users size={16} /><span>{t.header.effectiveDate}</span></div>
          </div>
        </header>

        <section className="mb-16">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {t.infoCards.map((card: { title: string; description: string }, index: number) => (
              <InfoSection
                key={index}
                icon={[<ShieldCheck size={24}/>, <Lock size={24}/>, <Eye size={24}/>, <Users size={24}/>][index]}
                title={card.title}
                description={card.description}
                bgColor={['bg-blue-50/80 dark:bg-blue-900/20', 'bg-green-50/80 dark:bg-green-900/20', 'bg-purple-50/80 dark:bg-purple-900/20', 'bg-red-50/80 dark:bg-red-900/20'][index]}
              />
            ))}
          </div>
        </section>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-12">
          <div className="lg:col-span-1">
            <TableOfContents sections={sections} activeSection={activeSection} onSectionClick={handleSectionClick} dictionary={dictionary} />
          </div>
          <div className="lg:col-span-3">
            <div className="bg-white/60 dark:bg-gray-800/40 backdrop-blur-sm rounded-3xl shadow-2xl p-8 md:p-12 border border-amber-200/50 dark:border-amber-700/30">
              <article className="prose prose-lg dark:prose-invert max-w-none">
                {t.sections.map((section: any, index: number) => (
                  <section key={section.id} id={section.id} className="mb-12 scroll-mt-20">
                    <h2 className="text-3xl font-bold text-gray-800 dark:text-gray-100 mb-6 flex items-center gap-3">
                      <div className="w-10 h-10 bg-gradient-to-r from-amber-500 to-green-500 rounded-xl flex items-center justify-center">
                        <span className="text-white font-bold">{index + 1}</span>
                      </div>
                      {section.title}
                    </h2>
                    {section.content && <div className="bg-amber-50 dark:bg-amber-900/20 rounded-2xl p-6 border border-amber-200 dark:border-amber-700/30 mb-6"><p className="text-gray-700 dark:text-gray-300 leading-relaxed text-lg">{section.content}</p></div>}
                    {section.intro && <p className="text-gray-700 dark:text-gray-300 leading-relaxed mb-4">{section.intro}</p>}
                    {section.points && <InteractiveList type={['data-usage', 'data-security'].includes(section.id) ? 'checks' : 'bullets'} items={section.points} />}
                    {section.commitmentTitle && <div className="bg-red-50 dark:bg-red-900/20 rounded-2xl p-6 border border-red-200 dark:border-red-700/30 mb-4"><h3 className="font-bold text-red-800 dark:text-red-200 mb-2 flex items-center gap-2"><Lock size={20} />{section.commitmentTitle}</h3><p className="text-red-700 dark:text-red-300 leading-relaxed">{section.commitmentText}</p></div>}
                    {section.rights && (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {section.rights.map((right: { title: string; description: string }, rIndex: number) => (
                          <div key={rIndex} className={`p-4 rounded-xl border ${['bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-700/30', 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-700/30', 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-700/30', 'bg-purple-50 dark:bg-purple-900/20 border-purple-200 dark:border-purple-700/30'][rIndex]}`}>
                            <h4 className={`font-bold mb-2 ${['text-blue-800 dark:text-blue-200', 'text-green-800 dark:text-green-200', 'text-red-800 dark:text-red-200', 'text-purple-800 dark:text-purple-200'][rIndex]}`}>{right.title}</h4>
                            <p className={`text-sm ${['text-blue-700 dark:text-blue-300', 'text-green-700 dark:text-green-300', 'text-red-700 dark:text-red-300', 'text-purple-700 dark:text-purple-300'][rIndex]}`}>{right.description}</p>
                          </div>
                        ))}
                      </div>
                    )}
                    {section.id === 'contact' && (
                      <>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                          <a href="mailto:privacy@syriagpt.com" className="flex items-center gap-4 p-6 bg-gradient-to-r from-amber-500 to-green-700 rounded-2xl text-white hover:from-amber-600 hover:to-green-600 transition-all duration-300 hover:scale-105 group">
                            <Mail size={24} className="group-hover:animate-pulse" />
                            <div><h3 className="font-bold text-lg">{section.email}</h3><p className="text-amber-100">privacy@syriagpt.com</p></div>
                          </a>
                          <a href="tel:+963123456789" className="flex items-center gap-4 p-6 bg-gradient-to-r from-green-500 to-green-700 rounded-2xl text-white hover:from-green-600 hover:to-green-700 transition-all duration-300 hover:scale-105 group">
                            <Phone size={24} className="group-hover:animate-pulse" />
                            <div><h3 className="font-bold text-lg">{section.phone}</h3><p className="text-blue-100">+963 123 456 789</p></div>
                          </a>
                        </div>
                        <p className="text-gray-600 dark:text-gray-400 text-center mt-6">{section.availability}</p>
                      </>
                    )}
                  </section>
                ))}
              </article>
            </div>
          </div>
        </div>

        <button onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })} className="fixed bottom-8 left-8 w-12 h-12 bg-gradient-to-r from-amber-500 to-green-500 rounded-full flex items-center justify-center text-white shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-110 z-20">
          <ArrowUp size={20} />
        </button>
      </div>

      <style jsx>{`
        @keyframes blob { 0% { transform: translate(0px, 0px) scale(1); } 33% { transform: translate(30px, -50px) scale(1.1); } 66% { transform: translate(-20px, 20px) scale(0.9); } 100% { transform: translate(0px, 0px) scale(1); } }
        @keyframes float { 0%, 100% { transform: translateY(0px); } 50% { transform: translateY(-10px); } }
        .animate-blob { animation: blob 7s infinite; }
        .animation-delay-2000 { animation-delay: 2s; }
        .animation-delay-4000 { animation-delay: 4s; }
        .animate-float { animation: float 3s ease-in-out infinite; }
        .scroll-mt-20 { scroll-margin-top: 5rem; /* 80px */ }
      `}</style>
    </main>
  );
}