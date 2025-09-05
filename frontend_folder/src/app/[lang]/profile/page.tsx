// src/app/[lang]/profile/page.tsx

import type { Metadata } from 'next';
import { getDictionary } from '../../../../get-dictionary';
import { Locale } from '../../../../i18n-config';
import ProfilePageClient from './ProfilePageClient'; // استيراد مكون العميل
import ProtectedRoute from '../components/ProtectedRoute';

// =======================
// دالة ديناميكية لإنشاء بيانات الميتا (العنوان والوصف) المترجمة
// =======================
// هذه الدالة مهمة جداً لمحركات البحث (SEO) ولعنوان التبويب في المتصفح
export async function generateMetadata({ params: { lang } }: { params: { lang: Locale } }): Promise<Metadata> {
  // 1. جلب القاموس للغة المحددة
  const dictionary = await getDictionary(lang);
  // 2. الوصول إلى نصوص الميتا المترجمة
  const t = dictionary.profilePage.metadata;
  // 3. إرجاع العنوان والوصف المترجمين
  return {
    title: t.title,
    description: t.description,
  };
}

// الحارس
export default async function ProfilePage({ params: awaitedParams }) {
  const params = await awaitedParams;
  const { lang } = params;
  const dictionary = await getDictionary(lang);

  return (
    <ProtectedRoute> {/* <-- 2. تغليف المكون */}
      <ProfilePageClient dictionary={dictionary} />
    </ProtectedRoute>
  );
}