// src/app/[lang]/page.tsx
import { getDictionary } from '../../../get-dictionary';
import { Locale } from '../../../i18n-config';
import ChatPageClient from './components/ChatPageClient';
import HomePageClient from './components/HomePageClient';

export default async function HomePage({
  params: awaitedParams, // <-- تغيير اسم المتغير
}: {
  params: { lang: Locale };
}) {
  // --- الحل الجديد والمؤكد هنا ---
  const params = await awaitedParams; // <-- انتظر الـ props
  const lang = params.lang;           // <-- ثم استخرج اللغة

  const dictionary = await getDictionary(lang);

  return <HomePageClient dictionary={dictionary} />;
}