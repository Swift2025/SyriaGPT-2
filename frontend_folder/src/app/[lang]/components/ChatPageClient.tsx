// src/app/[lang]/components/ChatPageClient.tsx
'use client';

import React, { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import MainContent from './MainContent';
import { Message, FileAttachment, Chat } from '../types';
import { getChatMessages, sendMessage, getChat, updateChat, deleteChat, deleteMessage } from '../../../../services/api';
import { useAuth } from '../../../context/AuthContext';
import toast from 'react-hot-toast';

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
  
  const { user } = useAuth();
  const t = dictionary.chat;

  // جلب الرسائل السابقة عند تحميل الصفحة أو تغيير chatId
  useEffect(() => {
    const fetchMessages = async () => {
      if (chatId && user) {
        setIsLoadingHistory(true);
        try {
          const data = await getChatMessages(chatId);
          // تحويل الرسائل من شكل الـ API إلى شكل الواجهة
          const formattedMessages = data.data?.messages?.map((msg: any) => ({
            id: msg.id,
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
    if (!chatId) return;
    
    const content = inputMessage.trim();
    if (!content || isLoading) return;

    setIsLoading(true);
    setInputMessage('');

    // إضافة رسالة المستخدم فوراً للواجهة لتحسين التجربة
    const userMessage: Message = { 
      id: `temp-${Date.now()}`, // استخدام ID مؤقت
      content, 
      sender: 'user', 
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMessage]);

    try {
      const response = await sendMessage(chatId, { message: content });
      
      // استبدال الرسالة المؤقتة بالرسالة الحقيقية
      // وإضافة رد الـ AI
      setMessages(prev => {
        const newMessages = prev.filter(m => m.id !== userMessage.id);
        const finalUserMessage = { ...userMessage, id: response.message.id };
        const aiResponse: Message = {
          id: response.ai_response.id,
          content: response.ai_response.message,
          sender: 'bot',
          timestamp: new Date(response.ai_response.created_at),
        };
        return [...newMessages, finalUserMessage, aiResponse];
      });

    } catch (error: any) {
      console.error('API error:', error);
      const errorMessageContent = error.message || t.networkError;
      const errorMessage: Message = { id: `error-${Date.now()}`, content: errorMessageContent, sender: 'bot', timestamp: new Date() };
      setMessages(prev => [...prev, errorMessage]);
      toast.error(errorMessageContent);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegenerate = async () => {
    if (!chatId || isLoading) return;
    
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
      
      // Send the last user message again
      const response = await sendMessage(chatId, { message: lastUserMessage.content });
      
      const aiResponse: Message = {
        id: response.ai_response.id,
        content: response.ai_response.message,
        sender: 'bot',
        timestamp: new Date(response.ai_response.created_at),
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
  );
}