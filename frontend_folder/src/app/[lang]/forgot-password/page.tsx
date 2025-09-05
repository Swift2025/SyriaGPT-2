// src/app/[lang]/forgot-password/page.tsx

import type { Metadata } from 'next';
import { getDictionary } from '../../../../get-dictionary';
import { Locale } from '../../../../i18n-config';
import ForgotPasswordClient from './ForgotPasswordClient'; // استيراد مكون العميل

// =======================
// دالة ديناميكية لإنشاء بيانات الميتا (العنوان والوصف) المترجمة
// =======================
// هذه الدالة مهمة جداً لمحركات البحث (SEO) ولعنوان التبويب في المتصفح
export async function generateMetadata({ params: { lang } }: { params: { lang: Locale } }): Promise<Metadata> {
  // 1. جلب القاموس للغة المحددة
  const dictionary = await getDictionary(lang);
  // 2. الوصول إلى نصوص الميتا المترجمة
  const t = dictionary.forgotPasswordPage.metadata;
  // 3. إرجاع العنوان والوصف المترجمين
  return {
    title: t.title,
    description: t.description,
  };
}

// =======================
// المكون الرئيسي للصفحة (مكون خادم)
// =======================
export default async function ForgotPasswordPage({ params: { lang } }: { params: { lang: Locale } }) {
  // 1. جلب القاموس الكامل للصفحة
  const dictionary = await getDictionary(lang);
  
  // 2. عرض مكون العميل وتمرير القاموس إليه كـ prop
  // كل المنطق التفاعلي (useState, handleSubmit, etc.) موجود داخل ForgotPasswordClient
  return <ForgotPasswordClient dictionary={dictionary} />;
}