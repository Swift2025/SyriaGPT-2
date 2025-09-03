// src/app/[lang]/chat/page.tsx
import { redirect } from 'next/navigation';
import { Locale } from '../../../../i18n-config';

interface PageProps {
  params: Promise<{ lang: Locale }>;
}

export default async function ChatPage({
  params,
}: PageProps) {
  const { lang } = await params;
  
  // Redirect to home page since chat functionality is handled there
  redirect(`/${lang}`);
}
