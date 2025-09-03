// src/app/[lang]/upgrade/page.tsx
import type { Metadata } from 'next';
import { getDictionary } from '../../../../get-dictionary';
import { Locale } from '../../../../i18n-config';
import UpgradePageClient from './UpgradePageClient'; // استيراد مكون العميل

// دالة ديناميكية لإنشاء بيانات الميتا المترجمة
export async function generateMetadata({ params }: { params: Promise<{ lang: Locale }> }): Promise<Metadata> {
  const { lang } = await params;
  const dictionary = await getDictionary(lang);
  const t = dictionary.upgradePage.metadata;
  return {
    title: t.title,
    description: t.description,
  };
}

// مكون الصفحة (خادم)
export default async function UpgradePage({ params }: { params: Promise<{ lang: Locale }> }) {
  const { lang } = await params;
  const dictionary = await getDictionary(lang);
  return <UpgradePageClient dictionary={dictionary} />;
}