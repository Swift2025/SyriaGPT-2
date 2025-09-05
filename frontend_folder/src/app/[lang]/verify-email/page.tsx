// src/app/[lang]/verify-email/page.tsx
import type { Metadata } from 'next';
import { getDictionary } from '../../../../get-dictionary';
import { Locale } from '../../../../i18n-config';
import VerifyEmailClient from './VerifyEmailClient';

// --- أضف هذا السطر ---
// هذا يخبر Next.js بأن هذه الصفحة ديناميكية ولا يجب إنشاؤها مسبقًا
export const dynamic = 'force-dynamic';
// --------------------

// دالة ديناميكية لإنشاء بيانات الميتا المترجمة
export async function generateMetadata({ params: { lang } }: { params: { lang: Locale } }): Promise<Metadata> {
  const dictionary = await getDictionary(lang);
  const t = dictionary.verifyEmailPage.metadata;
  return {
    title: t.title,
    description: t.description,
  };
}

// مكون الصفحة (خادم)
export default async function VerifyEmailPage({ params: { lang } }: { params: { lang: Locale } }) {
  const dictionary = await getDictionary(lang);
  return <VerifyEmailClient dictionary={dictionary} />;
}