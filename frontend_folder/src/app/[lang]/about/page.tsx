// src/app/[lang]/about/page.tsx

import type { Metadata } from 'next';
import Link from 'next/link';
import { ArrowRight } from 'lucide-react';
import { getDictionary } from '../../../../get-dictionary';
import { Locale } from '../../../../i18n-config';

// دالة ديناميكية لإنشاء بيانات الميتا (العنوان والوصف) المترجمة
export async function generateMetadata({ params: { lang } }: { params: { lang: Locale } }): Promise<Metadata> {
  const dictionary = await getDictionary(lang);
  const t = dictionary.aboutPage.metadata;
  return {
    title: t.title,
    description: t.description,
  };
}

// =======================
// المكون الرئيسي لصفحة "عن المشروع" (أصبح مكون خادم)
// =======================
export default async function AboutPage({ params: { lang } }: { params: { lang: Locale } }) {
  // جلب القاموس بناءً على اللغة من الرابط
  const dictionary = await getDictionary(lang);
  const t = dictionary.aboutPage;

  return (
    <div className="max-w-7xl mx-auto p-8 md:p-12 lg:p-16 text-brand-text-dark dark:text-brand-cream">
      
      <header className="flex justify-between items-center pb-8 border-b border-black/10 dark:border-white/10">
        <div className="flex items-center gap-4 animate-[fadeIn_1s_ease-in-out]">
          <img src="/images/logo.ai.svg" alt="شعار الجمهورية العربية السورية" className="h-16 md:h-20" />
          <div className="text-right">
            <h1 className="text-2xl md:text-3xl font-bold tracking-wider">{t.header.title}</h1>
            <p className="text-lg md:text-xl text-brand-text-gray dark:text-brand-cream/80 tracking-widest">{t.header.subtitle}</p>
          </div>
        </div>
        <div className="relative text-center animate-[fadeIn_1.5s_ease-in-out]">
          <img src="/images/map-header.png" alt="خريطة سوريا" className="w-24 md:w-32 drop-shadow-lg" />
          <p className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full text-lg font-semibold text-white">
            {t.header.mapText}
          </p>
        </div>
      </header>

      <main className="mt-12 grid grid-cols-1 lg:grid-cols-5 gap-12">
        <div className="lg:col-span-3 leading-loose space-y-6 text-justify animate-[fadeIn_2s_ease-in-out]">
          <p>{t.main.p1}</p>
          <p>{t.main.p2}</p>
          <p>{t.main.p3}</p>
        </div>
        <div className="lg:col-span-2 flex items-center justify-center relative animate-[fadeIn_2.5s_ease-in-out]">
          <img 
            src="/images/eagle-main.png" 
            alt="النسر السوري الذهبي" 
            className="w-full max-w-sm lg:max-w-md drop-shadow-[0_10px_20px_rgba(0,0,0,0.4)]"
          />
        </div>
      </main>

      <footer className="mt-16 flex flex-col items-center text-center">
        <Link 
          href={`/${lang}`} // رابط ديناميكي يعود للصفحة الرئيسية باللغة الحالية
          className="px-8 py-3 bg-brand-gold-primary/80 text-brand-teal-dark font-bold rounded-lg hover:bg-brand-gold-primary transition-all duration-300 hover:shadow-lg hover:scale-105 active:scale-95 flex items-center gap-2"
        >
          <ArrowRight size={18} />
          <span>{t.footer.backButton}</span>
        </Link>
        <p className="mt-8 text-sm text-brand-text-gray dark:text-brand-cream/60 max-w-3xl">
          {t.footer.disclaimer}
        </p>
      </footer>
    </div>
  );
}