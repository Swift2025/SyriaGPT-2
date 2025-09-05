// src/app/[lang]/chat/[chatId]/ChatPageClient.tsx
'use client';

import React, { useState, useEffect } from 'react';
import MainContent from './MainContent';
import { Message } from '../types';
import { getChatMessages, sendMessage } from '../../../../services/api';
import { useAuth } from '../../../context/AuthContext';
import toast from 'react-hot-toast';

interface ChatPageClientProps {
  toggleSidebar?: () => void;
  dictionary: any;
  chatId: string;
}

export default function ChatPageClient({ toggleSidebar, dictionary, chatId }: ChatPageClientProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingHistory, setIsLoadingHistory] = useState(true);
  
  const { user } = useAuth();
  const t = dictionary.chat;

  useEffect(() => {
    const fetchMessages = async () => {
      if (chatId && user) {
        setIsLoadingHistory(true);
        try {
          // --- تعديل حاسم: الواجهة الخلفية ترجع قائمة مباشرة ---
          const messagesFromApi = await getChatMessages(chatId);
          
          const formattedMessages = messagesFromApi.map((msg: any) => ({
            id: msg.id,
            content: msg.content, // <-- الواجهة الخلفية ترسل 'content'
            sender: msg.is_ai_response ? 'bot' : 'user',
            timestamp: new Date(msg.created_at),
          }));
          setMessages(formattedMessages);
        } catch (error: any) {
          toast.error(error.message || "Failed to load chat history.");
        } finally {
          setIsLoadingHistory(false);
        }
      }
    };
    fetchMessages();
  }, [chatId, user]);

  const handleSendMessage = async () => {
    const content = inputMessage.trim();
    if (!content || isLoading) return;

    setIsLoading(true);
    setInputMessage('');

    const userMessage: Message = { 
      id: `temp-${Date.now()}`,
      content, 
      sender: 'user', 
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMessage]);

    try {
      // --- تعديل حاسم: معالجة الاستجابة الجديدة ---
      const response = await sendMessage(chatId, { message: content });
      
      setMessages(prev => {
        const newMessages = prev.filter(m => m.id !== userMessage.id);
        
        const finalUserMessage: Message = {
          id: response.user_message.id,
          content: response.user_message.content,
          sender: 'user',
          timestamp: new Date(response.user_message.created_at),
        };

        const aiResponse: Message = {
          id: response.ai_message.id,
          content: response.ai_message.content,
          sender: 'bot',
          timestamp: new Date(response.ai_message.created_at),
        };
        
        return [...newMessages, finalUserMessage, aiResponse];
      });

    } catch (error: any) {
      const errorMessageContent = error.message || t.networkError;
      const errorMessage: Message = { id: `error-${Date.now()}`, content: errorMessageContent, sender: 'bot', timestamp: new Date() };
      setMessages(prev => [...prev, errorMessage]);
      toast.error(errorMessageContent);
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
      attachedFiles={[]}
      setAttachedFiles={() => {}}
      handleSendMessage={handleSendMessage}
      handleRegenerate={() => {}} // يمكنك إضافة منطق إعادة الإنشاء هنا لاحقًا
      isLoading={isLoading || isLoadingHistory}
      toggleSidebar={toggleSidebar || (() => {})}
    />
  );
}