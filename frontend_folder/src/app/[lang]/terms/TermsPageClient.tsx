// src/app/[lang]/terms/TermsPageClient.tsx
'use client';

import React, { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { ChevronUp, Shield, FileText, Users, Lock, Scale, AlertCircle, Mail, Calendar, Globe, Printer, Check, ChevronDown, ChevronRight } from 'lucide-react';

// --- أنواع البيانات ---
type Section = {
  id: string;
  title: string;
  icon: React.ReactNode;
  content: string;
};

// --- المكونات الفرعية ---

const TermsHeader: React.FC<{ t: any; onLanguageChange: () => void }> = ({ t, onLanguageChange }) => (
  <header className="sticky top-0 z-30 bg-brand-cream/90 dark:bg-brand-navy-dark/90 backdrop-blur-lg border-b border-black/5 dark:border-white/10 shadow-sm">
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
      <div className="flex justify-between items-center">
        <Link href="/" legacyBehavior>
          <a className="flex items-center gap-2">
            <div className="bg-brand-teal w-8 h-8 rounded-lg flex items-center justify-center">
              <img src="/images/logo.ai.svg" alt="SyriaGPT Logo" className="w-full h-full" style={{transform: 'scale(1.5)'}}/>
            </div>
            <span className="font-bold text-lg text-brand-text-dark dark:text-brand-cream hidden sm:inline">SyriaGPT</span>
          </a>
        </Link>
        <div className="flex items-center gap-2">
          <button 
            onClick={() => window.print()} 
            className="p-4 rounded-full hover:bg-black/5 dark:hover:bg-white/10 transition-colors"
            aria-label={t.header.print}
          >
            <Printer size={18} />
          </button>
        </div>
      </div>
    </div>
  </header>
);

const TermsSidebar: React.FC<{ 
  t: any; 
  activeSection: string; 
  scrollToSection: (id: string) => void;
  expandedSections: string[];
  toggleSection: (id: string) => void;
  expandAll: () => void;
  collapseAll: () => void;
  allExpanded: boolean;
}> = ({ t, activeSection, scrollToSection, expandedSections, toggleSection, expandAll, collapseAll, allExpanded }) => {
  const sectionIcons: { [key: string]: React.ReactNode } = {
    acceptance: <Shield size={18} />,
    services: <FileText size={18} />,
    usage: <Users size={18} />,
    privacy: <Lock size={18} />,
    intellectual: <Scale size={18} />,
    liability: <AlertCircle size={18} />,
    termination: <Calendar size={18} />,
    contact: <Mail size={18} />,
  };

  return (
    <aside className="lg:col-span-1">
      <div className="sticky top-24 bg-white dark:bg-gray-800/50 rounded-xl shadow-sm border border-black/5 dark:border-white/10 p-4">
        <div className="flex justify-between items-center mb-4">
          <h3 className="font-bold text-brand-text-dark dark:text-brand-cream">{t.sectionsTitle}</h3>
          <button onClick={allExpanded ? collapseAll : expandAll} className="text-xs text-brand-teal-primary hover:text-brand-teal-dark dark:hover:text-brand-teal-primary transition-colors">
            {allExpanded ? t.collapseAll : t.expandAll}
          </button>
        </div>
        <nav className="space-y-1">
          {t.sections.map((section: Section) => (
            <button
              key={section.id}
              onClick={() => { scrollToSection(section.id); toggleSection(section.id); }}
              className={`w-full text-right px-3 py-2 rounded-lg transition-all flex items-center gap-2 text-sm ${activeSection === section.id ? 'bg-brand-teal-primary/10 text-brand-teal-primary font-semibold' : 'hover:bg-black/5 dark:hover:bg-white/10 text-brand-text-gray dark:text-gray-300'}`}
            >
              <div className="flex-shrink-0">{expandedSections.includes(section.id) ? <ChevronDown size={16} /> : <ChevronRight size={16} />}</div>
              <div className="p-1.5 bg-brand-teal-primary/10 text-brand-teal-primary rounded-md">{sectionIcons[section.id]}</div>
              <span className="flex-1 text-right">{section.title}</span>
            </button>
          ))}
        </nav>
      </div>
    </aside>
  );
};

const TermsSection: React.FC<{ 
  section: Section; 
  isExpanded: boolean;
  onToggle: () => void;
}> = ({ section, isExpanded, onToggle }) => {
    const sectionIcons: { [key: string]: React.ReactNode } = {
    acceptance: <Shield size={18} />,
    services: <FileText size={18} />,
    usage: <Users size={18} />,
    privacy: <Lock size={18} />,
    intellectual: <Scale size={18} />,
    liability: <AlertCircle size={18} />,
    termination: <Calendar size={18} />,
    contact: <Mail size={18} />,
  };

  return (
    <div id={section.id} className="terms-section bg-white dark:bg-gray-800/50 rounded-xl shadow-sm border border-black/5 dark:border-white/10 mb-4 scroll-mt-24 transition-all duration-300">
      <button onClick={onToggle} className="w-full text-left p-5 flex items-center justify-between" aria-expanded={isExpanded}>
        <div className="flex items-center">
          <div className="p-2 bg-brand-teal-primary/10 text-brand-teal-primary rounded-lg mr-3">{sectionIcons[section.id]}</div>
          <h3 className="text-lg font-bold text-brand-text-dark dark:text-brand-cream">{section.title}</h3>
        </div>
        <div className="text-brand-teal-primary">{isExpanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}</div>
      </button>
      <div className={`overflow-hidden transition-all duration-300 ease-in-out ${isExpanded ? 'max-h-[1000px] opacity-100' : 'max-h-0 opacity-0'}`}>
        <div className="px-5 pb-5 -mt-2">
          <div className="prose prose-sm dark:prose-invert max-w-none text-brand-text-gray dark:text-gray-300 leading-relaxed whitespace-pre-line border-t border-black/5 dark:border-white/10 pt-4">{section.content}</div>
        </div>
      </div>
    </div>
  );
};

// =======================
// المكون الرئيسي للصفحة
// =======================
export default function TermsPageClient({ dictionary }: { dictionary: any }) {
  const [activeSection, setActiveSection] = useState('');
  const [acceptedTerms, setAcceptedTerms] = useState(false);
  const [expandedSections, setExpandedSections] = useState<string[]>([]);
  const [readingProgress, setReadingProgress] = useState(0);
  const [allExpanded, setAllExpanded] = useState(false);
  
  const params = useParams();
  const router = useRouter();
  const lang = params.lang as string;
  const t = dictionary.termsPage;

  const handleLanguageChange = () => {
    const newLang = lang === 'ar' ? 'en' : 'ar';
    router.push(`/${newLang}/terms`);
  };

  useEffect(() => {
    const handleScroll = () => {
      const winScroll = document.body.scrollTop || document.documentElement.scrollTop;
      const height = document.documentElement.scrollHeight - document.documentElement.clientHeight;
      const scrolled = (winScroll / height) * 100;
      setReadingProgress(scrolled);
      
      const sections = document.querySelectorAll('.terms-section');
      let currentSection = '';
      sections.forEach((section) => {
        const sectionTop = (section as HTMLElement).offsetTop;
        if (window.scrollY >= sectionTop - 100) {
          currentSection = section.id;
        }
      });
      setActiveSection(currentSection);
    };
    
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const scrollToSection = (sectionId: string) => {
    document.getElementById(sectionId)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  const toggleSection = (sectionId: string) => {
    setExpandedSections(prev => prev.includes(sectionId) ? prev.filter(id => id !== sectionId) : [...prev, sectionId]);
  };

  const expandAll = () => { setExpandedSections(t.sections.map((s: Section) => s.id)); setAllExpanded(true); };
  const collapseAll = () => { setExpandedSections([]); setAllExpanded(false); };

  return (
    <div className="bg-brand-cream dark:bg-brand-navy-dark text-brand-text-dark dark:text-brand-cream min-h-screen flex flex-col">
      <div className="fixed top-0 left-0 w-full h-1 bg-gray-200 dark:bg-gray-700 z-20">
        <div className="h-full bg-brand-teal-primary transition-all duration-300 ease-out" style={{ width: `${readingProgress}%` }}></div>
      </div>
      
      <TermsHeader t={t} onLanguageChange={handleLanguageChange} />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex-grow">
        <div className="text-center mb-8">
          <h1 className="text-3xl md:text-4xl font-bold text-brand-text-dark dark:text-brand-cream mb-2">{t.title}</h1>
          <p className="text-brand-text-gray dark:text-gray-400">{t.subtitle}</p>
          <div className="mt-4 inline-flex items-center bg-brand-teal-primary/10 text-brand-teal-primary px-3 py-1 rounded-full text-sm">
            <span>{t.readingProgress}: {Math.round(readingProgress)}%</span>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          <TermsSidebar t={t} activeSection={activeSection} scrollToSection={scrollToSection} expandedSections={expandedSections} toggleSection={toggleSection} expandAll={expandAll} collapseAll={collapseAll} allExpanded={allExpanded} />

          <main className="lg:col-span-3">
            <div className="bg-white dark:bg-gray-800/50 rounded-xl shadow-sm border border-black/5 dark:border-white/10 p-6 mb-6">
              <p className="leading-relaxed text-brand-text-gray dark:text-gray-300">{t.intro}</p>
            </div>

            <div className="space-y-4">
              {t.sections.map((section: Section) => (
                <TermsSection key={section.id} section={section} isExpanded={expandedSections.includes(section.id)} onToggle={() => toggleSection(section.id)} />
              ))}
            </div>

            <div className="bg-white dark:bg-gray-800/50 rounded-xl shadow-sm border border-black/5 dark:border-white/10 p-6 mt-6 sticky bottom-4">
              <div className="flex items-start mb-4">
                <input type="checkbox" id="accept-terms" checked={acceptedTerms} onChange={(e) => setAcceptedTerms(e.target.checked)} className="w-5 h-5 text-brand-teal-primary bg-gray-100 border-gray-300 rounded focus:ring-brand-teal-primary dark:focus:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600 mt-0.5" />
                <label htmlFor="accept-terms" className="mr-3 text-sm font-medium text-brand-text-gray dark:text-gray-300">{t.acceptButton}</label>
              </div>
              <button disabled={!acceptedTerms} onClick={() => alert('Accepted!')} className={`w-full py-3 px-6 rounded-lg font-semibold transition-all flex items-center justify-center ${acceptedTerms ? 'bg-brand-teal-primary hover:bg-brand-teal-dark text-white shadow-md hover:shadow-lg transform hover:-translate-y-0.5' : 'bg-gray-300 dark:bg-gray-600 text-gray-500 dark:text-gray-400 cursor-not-allowed'}`}>
                {acceptedTerms ? (<><Check size={20} className="ml-2" />{t.continueButton}</>) : t.continueButton}
              </button>
            </div>
          </main>
        </div>
      </div>

      <footer className="py-6 text-center border-t border-black/5 dark:border-white/10">
        <button onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })} className="inline-flex items-center px-4 py-2 bg-white dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors text-sm shadow-sm">
          <ChevronUp className="ml-2" size={16} />
          {t.backToTop}
        </button>
        <p className="mt-4 text-sm text-brand-text-gray dark:text-gray-400">
          {t.copyright.replace('{year}', new Date().getFullYear())}
        </p>
      </footer>
    </div>
  );
};