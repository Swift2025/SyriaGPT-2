// src/app/[lang]/page.tsx
import { getDictionary } from '../../../get-dictionary';
import { Locale } from '../../../i18n-config';
import ChatPageClient from './components/ChatPageClient';

interface PageProps {
  params: Promise<{ lang: Locale }>;
}

export default async function HomePage({
  params,
}: PageProps) {
  const { lang } = await params;
  const dictionary = await getDictionary(lang);

  return <ChatPageClient dictionary={dictionary} />;
}