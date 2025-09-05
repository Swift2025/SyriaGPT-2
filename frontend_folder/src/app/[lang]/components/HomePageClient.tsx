// src/app/[lang]/components/HomePageClient.tsx
'use client';

import React, { useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import MainContent from './MainContent'; // تم تصحيح المسار
import { createChat, sendMessage } from '../../../../services/api';
import { useAuth } from '../../../context/AuthContext';
import toast from 'react-hot-toast';

export default function HomePageClient({ dictionary }: { dictionary: any }) {
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  const router = useRouter();
  const params = useParams();
  const lang = params.lang as string;
  const { user } = useAuth();

  const handleFirstSendMessage = async () => {
    const content = inputMessage.trim();
    if (!content || isLoading) return;

    if (!user) {
      toast.error(dictionary.errors?.loginRequired || "You must be logged in to start a chat.");
      router.push(`/${lang}/login`);
      return;
    }

    setIsLoading(true);
    setInputMessage('');

    try {
      // الخطوة 1: إنشاء محادثة جديدة
      const newChatData = await createChat({ title: content.substring(0, 40) });
      
      // --- تعديل حاسم: الوصول إلى 'id' مباشرة ---
      const chatId = newChatData.id;

      // الخطوة 2: إرسال الرسالة الأولى إلى هذه المحادثة الجديدة
      await sendMessage(chatId, { message: content });

      // الخطوة 3: توجيه المستخدم إلى صفحة المحادثة الجديدة
      // هذه الصفحة ستقوم بجلب سجل المحادثة بالكامل
      router.push(`/${lang}/chat/${chatId}`);

    } catch (error: any) {
      toast.error(error.message || "Failed to start a new chat.");
      setIsLoading(false);
    }
  };

  return (
    <MainContent
      dictionary={dictionary}
      messages={[]} // الصفحة الرئيسية لا تحتوي على رسائل
      inputMessage={inputMessage}
      setInputMessage={setInputMessage}
      attachedFiles={[]}
      setAttachedFiles={() => {}}
      handleSendMessage={handleFirstSendMessage} // استخدام الدالة المخصصة للصفحة الرئيسية
      handleRegenerate={() => {}}
      isLoading={isLoading}
      toggleSidebar={() => {}}
    />
  );
}