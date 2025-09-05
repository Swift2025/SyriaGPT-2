// src/app/[lang]/check-email/page.tsx
import { getDictionary } from '../../../../get-dictionary';
import { Locale } from '../../../../i18n-config';
import CheckEmailClient from './CheckEmailClient';

// --- أضف هذا السطر ---
// هذا يخبر Next.js بأن هذه الصفحة ديناميكية ولا يجب إنشاؤها مسبقًا
export const dynamic = 'force-dynamic';
// --------------------

export default async function CheckEmailPage({ params: { lang } }: { params: { lang: Locale } }) {
  const dictionary = await getDictionary(lang);
  return <CheckEmailClient dictionary={dictionary} />;
}