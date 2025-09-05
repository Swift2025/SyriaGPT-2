// src/app/[lang]/layout.tsx
import type { Metadata } from 'next';
import { Noto_Sans_Arabic } from 'next/font/google';
import { i18n, type Locale } from '../../../i18n-config';
import { getDictionary } from '../../../get-dictionary';
import ClientLayout from './components/ClientLayout';
import './globals.css';

const notoArabic = Noto_Sans_Arabic({
  subsets: ['arabic'],
  weight: ['400', '500', '700'],
  display: 'swap',
});

export async function generateStaticParams() {
  return i18n.locales.map((locale) => ({ lang: locale }));
}

export const metadata: Metadata = {
  title: 'SyriaGPT',
  description: 'SyriaGPT Chatbot',
  icons: {
    icon: '/logo.ai.svg', // مسار الأيقونة
  },
};

export default async function RootLayout({
  children,
  params: awaitedParams,
}: {
  children: React.ReactNode;
  params: { lang: Locale };
}) {
  const params = await awaitedParams;
  const lang = params.lang;

  const dictionary = await getDictionary(lang);

  return (
    <html lang={lang} dir={lang === 'ar' ? 'rtl' : 'ltr'} suppressHydrationWarning>
      <body className={`${notoArabic.className} antialiased`}>
        <ClientLayout dictionary={dictionary}>
          {children}
        </ClientLayout>
      </body>
    </html>
  );
}