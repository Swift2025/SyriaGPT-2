// src/app/[lang]/register/page.tsx
import type { Metadata } from 'next';
import { getDictionary } from '../../../../get-dictionary';
import { Locale } from '../../../../i18n-config';
import RegisterPageClient from './RegisterPageClient'; // استيراد مكون العميل

// دالة ديناميكية لإنشاء بيانات الميتا المترجمة
export async function generateMetadata({ params }: { params: Promise<{ lang: Locale }> }): Promise<Metadata> {
  const { lang } = await params;
  const dictionary = await getDictionary(lang);
  const t = dictionary.registerPage.metadata;
  return {
    title: t.title,
    description: t.description,
  };
}

// مكون الصفحة (خادم)
export default async function RegisterPage({ params }: { params: Promise<{ lang: Locale }> }) {
  const { lang } = await params;
  const dictionary = await getDictionary(lang);
  return <RegisterPageClient dictionary={dictionary} />;
}