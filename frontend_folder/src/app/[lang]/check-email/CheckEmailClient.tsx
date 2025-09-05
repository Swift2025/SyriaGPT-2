'use client';

import React from 'react';
import { useSearchParams, useParams } from 'next/navigation';
import { Mail, CheckCircle } from 'lucide-react';
import Link from 'next/link';

export default function CheckEmailClient({ dictionary }: { dictionary: any }) {
  const searchParams = useSearchParams();
  const params = useParams();
  const lang = params.lang as string;
  const email = searchParams.get('email');
  const t = dictionary.checkEmailPage; // ستحتاج إلى إضافة هذه الترجمات في ملفات .json

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 p-4">
      <div className="w-full max-w-md bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-8 text-center">
        <div className="w-20 h-20 bg-green-100 dark:bg-green-900/20 rounded-full flex items-center justify-center mx-auto mb-6">
          <CheckCircle className="w-12 h-12 text-green-500" />
        </div>
        <h1 className="text-2xl font-bold text-gray-800 dark:text-white mb-4">{t.title}</h1>
        <p className="text-gray-600 dark:text-gray-400 mb-6">
          {t.description.part1} <span className="font-semibold text-amber-600 dark:text-amber-400 break-all">{email}</span>. {t.description.part2}
        </p>
        <div className="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-4 mb-6">
          <p className="text-sm text-gray-500 dark:text-gray-300">{t.spamTip}</p>
        </div>
        <Link href={`/${lang}/login`}>
          <button className="w-full py-3 px-4 rounded-lg font-semibold text-white bg-teal-600 hover:bg-teal-700">
            {t.backToLoginButton}
          </button>
        </Link>
      </div>
    </div>
  );
}