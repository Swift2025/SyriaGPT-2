// src/app/[lang]/settings/page.tsx
import type { Metadata } from 'next';
import { getDictionary } from '../../../../get-dictionary';
import { Locale } from '../../../../i18n-config';
import SettingsPageClient from './SettingsPageClient'; // استيراد مكون العميل
import ProtectedRoute from '../components/ProtectedRoute'; // <-- 1. استيراد الحارس

// دالة ديناميكية لإنشاء بيانات الميتا المترجمة
export async function generateMetadata({ params: { lang } }: { params: { lang: Locale } }): Promise<Metadata> {
  const dictionary = await getDictionary(lang);
  const t = dictionary.settingsPage.metadata;
  return {
    title: t.title,
    description: t.description,
  };
}


// الحارس
export default async function SettingsPage({ params: awaitedParams }) {
  const params = await awaitedParams;
  const { lang } = params;
  const dictionary = await getDictionary(lang);

  return (
    <ProtectedRoute> {/* <-- 2. تغليف المكون */}
      <SettingsPageClient dictionary={dictionary} />
    </ProtectedRoute>
  );
}