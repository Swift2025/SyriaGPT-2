// src/app/[lang]/components/ChatPageClient.tsx
'use client';

import React, { useState, useEffect, useId } from 'react';
import { useParams, useRouter } from 'next/navigation';
import MainContent from './MainContent';
import ProtectedRoute from './ProtectedRoute';
import { Message, FileAttachment, Chat } from '../types';
import { getChatMessages, sendMessage, getChat, updateChat, deleteChat, deleteMessage, apiFetch } from '../../../../services/api';
import { useAuth } from '../../../context/AuthContext';
// import { searchAnswer } from '../../../../services/searchService';
import toast from 'react-hot-toast';

// دالة مساعدة لإنشاء ID فريد (يعمل فقط على العميل)
const generateUniqueId = (prefix: string = 'msg', isClient: boolean = false, baseId: string = ''): string => {
  // استخدام ID ثابت للخادم لتجنب hydration mismatch
  if (!isClient) {
    return `${prefix}-server-${baseId}`;
  }
  return `${prefix}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
};

interface ChatPageClientProps {
  toggleSidebar?: () => void;
  dictionary: any;
  chatId?: string;
}

export default function ChatPageClient({ toggleSidebar, dictionary, chatId }: ChatPageClientProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingHistory, setIsLoadingHistory] = useState(true);
  const [isClient, setIsClient] = useState(false);
  
  const { user } = useAuth();
  const t = dictionary.chat;
  const baseId = useId();
  
  // Debug: مراقبة حالة المستخدم
  useEffect(() => {
    console.log('ChatPageClient - User state:', user);
    if (user) {
      console.log('ChatPageClient - User details:', {
        id: user.id,
        email: user.email,
        full_name: user.full_name,
        name: user.full_name || user.email
      });
    }
  }, [user]);

  // التأكد من أننا على العميل
  useEffect(() => {
    setIsClient(true);
  }, []);

  // جلب الرسائل السابقة عند تحميل الصفحة أو تغيير chatId
  useEffect(() => {
    const fetchMessages = async () => {
      if (chatId && user) {
        setIsLoadingHistory(true);
        try {
          const data = await getChatMessages(chatId);
          // تحويل الرسائل من شكل الـ API إلى شكل الواجهة
          const formattedMessages = data.data?.messages?.map((msg: any, index: number) => ({
            id: msg.id || generateUniqueId(`msg-${index}`, isClient, baseId),
            content: msg.message,
            sender: msg.is_ai_response ? 'bot' : 'user',
            timestamp: new Date(msg.created_at),
          })) || [];
          setMessages(formattedMessages);
        } catch (error: any) {
          toast.error(error.message || "Failed to load chat history.");
        } finally {
          setIsLoadingHistory(false);
        }
      } else if (!user) {
        setIsLoadingHistory(false);
      }
    };
    fetchMessages();
  }, [chatId, user]);

  const handleSendMessage = async () => {
    const content = inputMessage.trim();
    if (!content || isLoading) return;

    setIsLoading(true);
    setInputMessage('');

    // إضافة رسالة المستخدم فوراً للواجهة لتحسين التجربة
    const userMessage: Message = { 
      id: generateUniqueId('temp-user', isClient, baseId),
      content, 
      sender: 'user', 
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMessage]);

    try {
      // استخدام خدمة البحث الجديدة
      const response = await fetch('/api/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: content
        }),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      // إضافة رد الـ AI
      const aiResponse: Message = {
        id: generateUniqueId('ai', isClient, baseId),
        content: data.answer || 'لم أتمكن من الحصول على إجابة',
        sender: 'bot',
        timestamp: new Date(),
        source: data.source,
        source_details: data.source_details
      };
      
      setMessages(prev => {
        const newMessages = prev.filter(m => m.id !== userMessage.id);
        const finalUserMessage = { ...userMessage, id: generateUniqueId('user', isClient, baseId) };
        return [...newMessages, finalUserMessage, aiResponse];
      });

    } catch (error: any) {
      console.error('API error:', error);
      
      // معالجة أفضل للأخطاء
      let errorMessageContent = t.networkError;
      if (error.message) {
        if (typeof error.message === 'string') {
          errorMessageContent = error.message;
        } else {
          errorMessageContent = JSON.stringify(error.message);
        }
      }
      
      const errorMessage: Message = { 
        id: generateUniqueId('error', isClient, baseId), 
        content: errorMessageContent, 
        sender: 'bot', 
        timestamp: new Date() 
      };
      setMessages(prev => [...prev, errorMessage]);
      toast.error(errorMessageContent);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegenerate = async () => {
    if (isLoading) return;
    
    // Find the last user message
    const lastUserMessage = messages.findLast(m => m.sender === 'user');
    if (!lastUserMessage) return;

    setIsLoading(true);
    
    try {
      // Remove the last AI response
      setMessages(prev => prev.filter(m => {
        if (prev.length === 0) return true;
        const lastMessage = prev[prev.length - 1];
        return lastMessage ? m.id !== lastMessage.id : true;
      }));
      
      // Send the last user message again using local API
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: lastUserMessage.content,
          conversationHistory: messages.slice(0, -1).map(msg => ({
            sender: msg.sender,
            content: msg.content
          }))
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      const aiResponse: Message = {
        id: generateUniqueId('ai', isClient, baseId),
        content: data.message,
        sender: 'bot',
        timestamp: new Date(),
        source: data.source,
        source_details: data.source_details
      };
      
      setMessages(prev => [...prev, aiResponse]);
      
    } catch (error: any) {
      console.error('Regeneration error:', error);
      toast.error(error.message || 'Failed to regenerate response');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <ProtectedRoute>
      <MainContent
        dictionary={dictionary}
        messages={messages}
        inputMessage={inputMessage}
        setInputMessage={setInputMessage}
        attachedFiles={[]} // رفع الملفات غير مدعوم حالياً في هذا المنطق
        setAttachedFiles={() => {}}
        handleSendMessage={handleSendMessage}
        handleRegenerate={handleRegenerate}
        isLoading={isLoading || isLoadingHistory} // إظهار التحميل أثناء جلب الرسائل أيضاً
        toggleSidebar={toggleSidebar || (() => {})}
      />
    </ProtectedRoute>
  );
}