// src/app/[lang]/components/MainContent.tsx
'use client';

import React, { useRef, useEffect, useState, useCallback } from 'react';
import { Send, Sun, Zap, AlertTriangle, User, Menu, ThumbsUp, ThumbsDown, RefreshCw, Mic, Paperclip, X, FileText, File, Upload, Download, Share2, Archive, Trash2 } from 'lucide-react';
import { speechService, requestMicrophonePermission } from '../utils/speechService';
import { addFeedbackToMessage } from '../../../../services/api';
import toast from 'react-hot-toast';
import { Message, FileAttachment } from '../types';

// دالة عرض اسم المصدر
const getSourceDisplayName = (source: string): string => {
  const sourceNames: { [key: string]: string } = {
    'gemini': 'Google Gemini AI',
    'advanced_fallback': 'النظام الاحتياطي المحسن',
    'fallback': 'النظام الاحتياطي الأساسي',
    'final_fallback': 'النظام الافتراضي',
    'identity_service': 'خدمة الهوية',
    'intelligent_qa': 'الخدمة الذكية',
    'error': 'خطأ في النظام',
    'emergency_error': 'نظام الطوارئ',
    'unknown': 'مصدر غير معروف'
  };
  return sourceNames[source] || source;
};

// مكون شعار النسر السوري
const SyrianEagle: React.FC<{ className?: string }> = ({ className = "w-12 h-12" }) => (
  <div className={`${className} flex items-center justify-center`} suppressHydrationWarning={true}>
    <img src="/logo.ai.svg" alt="Syrian Eagle Logo" className="w-full h-full" />
  </div>
);

// مكون أيقونة المستخدم
const UserIcon: React.FC<{ className?: string }> = ({ className = "w-10 h-10" }) => (
  <div className={`${className} flex items-center justify-center rounded-full bg-gradient-to-br from-teal-100 to-teal-200 dark:from-teal-900 dark:to-teal-800 p-2 shadow-lg`} suppressHydrationWarning={true}>
    <User size={18} className="text-teal-700 dark:text-teal-300" />
  </div>
);

// بطاقة الاقتراح
const SuggestionCard: React.FC<{ children: React.ReactNode; onClick: () => void }> = ({ children, onClick }) => (
  <button 
    onClick={onClick} 
    className="w-full p-4 rounded-xl border-2 border-amber-100 dark:border-amber-700 hover:border-amber-400 dark:hover:border-amber-500 bg-gradient-to-br from-amber-50 to-green-00 dark:from-gray-800 dark:to-gray-700 hover:from-amber-100 hover:to-green-100 dark:hover:bg-gray-700 transition-all duration-300 text-right text-sm text-gray-700 dark:text-gray-300 hover:text-amber-800 dark:hover:text-amber-300 shadow-sm hover:shadow-lg transform hover:scale-105 border-opacity-60 hover:border-opacity-100"
    suppressHydrationWarning={true}
  >
    {children}
  </button>
);

// معاينة الملف
const FilePreview: React.FC<{ file: FileAttachment; onRemove: () => void; dictionary: any }> = ({ file, onRemove, dictionary }) => {
  const t = dictionary.mainContent.input;
  
  const getFileIcon = (type: string) => {
    if (type.includes('pdf')) return <FileText className="w-5 h-5 text-red-500" />;
    if (type.includes('word')) return <FileText className="w-5 h-5 text-blue-500" />;
    return <File className="w-5 h-5 text-gray-500" />;
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
  };

  return (
    <div className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700" suppressHydrationWarning={true}>
      {getFileIcon(file.type)}
      <div className="flex-1 min-w-0" suppressHydrationWarning={true}>
        <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">{file.name}</p>
        <p className="text-xs text-gray-500 dark:text-gray-400">{formatFileSize(file.size)}</p>
      </div>
      <button 
        onClick={onRemove} 
        className="p-1 text-gray-400 hover:text-red-500 transition-colors"
        title={t.removeFile}
      >
        <X size={16} />
      </button>
    </div>
  );
};

// شاشة الترحيب
const WelcomeScreen: React.FC<{ onSuggestionClick: (suggestion: string) => void; dictionary: any }> = ({ onSuggestionClick, dictionary }) => {
  const t = dictionary.mainContent.welcome;
  const suggestions = t.suggestions;

  return (
    <div className="flex-1 flex flex-col items-center justify-center p-8 min-h-[60vh]" suppressHydrationWarning={true}>
      <div className="text-center mb-12" suppressHydrationWarning={true}>
        <SyrianEagle className="w-24 h-24 mx-auto mb-6" />
        <h1 className="text-5xl font-bold bg-gradient-to-r from-amber-700 via-amber-400 to-green-200 bg-clip-text text-transparent mb-4">{t.title}</h1>
        <p className="text-gray-600 dark:text-gray-400 text-lg">{t.tagline}</p>
      </div>
      <div className="w-full max-w-6xl" suppressHydrationWarning={true}>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8" suppressHydrationWarning={true}>
          <div className="text-center" suppressHydrationWarning={true}>
            <div className="flex items-center justify-center gap-2 mb-6" suppressHydrationWarning={true}><div className="p-2 bg-yellow-100 dark:bg-yellow-900 rounded-lg" suppressHydrationWarning={true}><Sun size={20} className="text-amber-600 dark:text-amber-400" /></div><h3 className="font-bold text-xl text-gray-800 dark:text-gray-200">{t.examples}</h3></div>
            <div className="space-y-3" suppressHydrationWarning={true}>{suggestions.examples.map((s: string) => <SuggestionCard key={s} onClick={() => onSuggestionClick(s)}>{s}</SuggestionCard>)}</div>
          </div>
          <div className="text-center" suppressHydrationWarning={true}>
            <div className="flex items-center justify-center gap-2 mb-6" suppressHydrationWarning={true}><div className="p-2 bg-green-100 dark:bg-green-900 rounded-lg" suppressHydrationWarning={true}><Zap size={20} className="text-green-600 dark:text-green-400" /></div><h3 className="font-bold text-xl text-gray-800 dark:text-gray-200">{t.capabilities}</h3></div>
            <div className="space-y-3" suppressHydrationWarning={true}>{suggestions.capabilities.map((s: string) => <SuggestionCard key={s} onClick={() => onSuggestionClick(s)}>{s}</SuggestionCard>)}</div>
          </div>
          <div className="text-center" suppressHydrationWarning={true}>
            <div className="flex items-center justify-center gap-2 mb-6" suppressHydrationWarning={true}><div className="p-2 bg-red-100 dark:bg-red-900 rounded-lg" suppressHydrationWarning={true}><AlertTriangle size={20} className="text-red-600 dark:text-red-400" /></div><h3 className="font-bold text-xl text-gray-800 dark:text-gray-200">{t.limitations}</h3></div>
            <div className="space-y-3" suppressHydrationWarning={true}>{suggestions.limitations.map((s: string) => <SuggestionCard key={s} onClick={() => onSuggestionClick(s)}>{s}</SuggestionCard>)}</div>
          </div>
        </div>
      </div>
    </div>
  );
};

// عنصر الرسالة
const MessageItem: React.FC<{ message: Message; dictionary: any }> = ({ message, dictionary }) => {
  const t = dictionary.mainContent.message;
  const isUser = message.sender === 'user';

  const handleFeedback = async (rating: number, type: string) => {
    try {
      await addFeedbackToMessage(message.id, { rating, feedback_type: type });
      toast.success("Thank you for your feedback!");
    } catch (error: any) {
      toast.error(error.message);
    }
  };
  
  return (
    <div className="w-full max-w-4xl mx-auto px-4 py-2" suppressHydrationWarning={true}>
      <div className={`flex items-start gap-4 ${isUser ? 'justify-end' : 'justify-start'}`} suppressHydrationWarning={true}>
        {!isUser && <SyrianEagle className="w-10 h-10 mt-1" />}
        <div className={`max-w-[80%] ${isUser ? 'order-first' : ''}`} suppressHydrationWarning={true}>
          {message.isTyping ? (
            <div className="flex items-center gap-2 p-4 bg-gray-100 dark:bg-gray-800 rounded-2xl" suppressHydrationWarning={true}>
              <div className="flex gap-1" suppressHydrationWarning={true}><div className="w-2 h-2 bg-amber-500 rounded-full animate-bounce" style={{animationDelay: '0ms'}} suppressHydrationWarning={true}></div><div className="w-2 h-2 bg-amber-500 rounded-full animate-bounce" style={{animationDelay: '150ms'}} suppressHydrationWarning={true}></div><div className="w-2 h-2 bg-amber-500 rounded-full animate-bounce" style={{animationDelay: '300ms'}} suppressHydrationWarning={true}></div></div>
              <span className="text-sm text-gray-600 dark:text-gray-400">{t.typing}</span>
            </div>
          ) : (
            <div className={`p-4 rounded-2xl ${isUser ? 'bg-gradient-to-r from-amber-500 to-green-500 text-white shadow-lg' : 'bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-200 border border-gray-200 dark:border-gray-700'}`} suppressHydrationWarning={true}>
              <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
              {!isUser && message.source && (
                <div className="mt-2 pt-2 border-t border-gray-200 dark:border-gray-600">
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    <span className="font-medium">المصدر:</span> {getSourceDisplayName(message.source)}
                  </p>
                </div>
              )}
            </div>
          )}
          {!isUser && !message.isTyping && (
            <div className="flex items-center gap-2 mt-2 px-2" suppressHydrationWarning={true}>
              <button onClick={() => handleFeedback(5, 'helpful')} className="p-1 text-gray-400 hover:text-green-500 transition-colors" suppressHydrationWarning={true}><ThumbsUp size={14} /></button>
              <button onClick={() => handleFeedback(1, 'unhelpful')} className="p-1 text-gray-400 hover:text-red-500 transition-colors" suppressHydrationWarning={true}><ThumbsDown size={14} /></button>
            </div>
          )}
        </div>
        {isUser && <UserIcon className="w-10 h-10 mt-1" />}
      </div>
    </div>
  );
};

// زر إعادة إنشاء الرد
const RegenerateResponse: React.FC<{ onRegenerate: () => void; dictionary: any }> = ({ onRegenerate, dictionary }) => (
  <div className="w-full max-w-4xl mx-auto px-4 py-2" suppressHydrationWarning={true}>
    <div className="flex justify-center" suppressHydrationWarning={true}>
      <button onClick={onRegenerate} className="flex items-center gap-2 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors" suppressHydrationWarning={true}>
        <RefreshCw size={14} />
        {dictionary.mainContent.regenerate}
      </button>
    </div>
  </div>
);

// منطقة إدخال الرسائل
const ChatInputArea: React.FC<{
  inputMessage: string;
  setInputMessage: (v: string) => void;
  attachedFiles: FileAttachment[];
  setAttachedFiles: (files: React.SetStateAction<FileAttachment[]>) => void;
  handleSendMessage: () => void;
  isLoading: boolean;
  dictionary: any;
  suppressHydrationWarning?: boolean;
}> = ({ inputMessage, setInputMessage, attachedFiles, setAttachedFiles, handleSendMessage, isLoading, dictionary, suppressHydrationWarning = false }) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [isDragOver, setIsDragOver] = useState(false);
  const t = dictionary.mainContent;

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [inputMessage]);

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if ((inputMessage.trim() || attachedFiles.length > 0) && !isLoading) {
        handleSendMessage();
      }
    }
  };

  const toggleRecording = async () => {
    if (typeof window === 'undefined') return;
    if (!speechService.isSupported()) { alert(t.speechErrors.unsupported); return; }
    if (isRecording) { speechService.stopListening(); setIsRecording(false); return; }
    try {
      const hasPermission = await requestMicrophonePermission();
      if (!hasPermission) { alert(t.speechErrors.permissionDenied); return; }
      const success = speechService.startListening({
        language: 'ar-SA',
        onStart: () => setIsRecording(true),
        onResult: (text: string, isFinal?: boolean) => { 
          if (isFinal && text.trim()) {
            const newText = inputMessage ? `${inputMessage} ${text}` : text;
            setInputMessage(newText.trim()); 
          }
        },
        onError: (error: string) => { const message = t.speechErrors[error] || `Unknown error: ${error}`; alert(message); },
        onEnd: () => setIsRecording(false),
      });
      if (!success) { alert(t.speechErrors.startFailed); setIsRecording(false); }
    } catch (error) { console.error('General recording error:', error); setIsRecording(false); alert(t.speechErrors.generalError); }
  };

  const handleFiles = (files: File[]) => {
    const newFiles: FileAttachment[] = files.filter(file => file.size <= 10 * 1024 * 1024).map((file, index) => ({ 
      id: `${file.name}-${index}-${Math.random().toString(36).substr(2, 9)}`, 
      name: file.name, 
      size: file.size, 
      type: file.type, 
      file: file 
    }));
    setAttachedFiles(prev => [...prev, ...newFiles]);
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => { if (e.target.files) handleFiles(Array.from(e.target.files)); };
  const removeFile = (fileId: string) => { setAttachedFiles(prev => prev.filter(f => f.id !== fileId)); };
  const handleDragOver = useCallback((e: React.DragEvent) => { e.preventDefault(); setIsDragOver(true); }, []);
  const handleDragLeave = useCallback((e: React.DragEvent) => { e.preventDefault(); setIsDragOver(false); }, []);
  const handleDrop = useCallback((e: React.DragEvent) => { e.preventDefault(); setIsDragOver(false); if (e.dataTransfer.files) handleFiles(Array.from(e.dataTransfer.files)); }, []);

  return (
    <div className="border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-4" onDragOver={handleDragOver} onDragLeave={handleDragLeave} onDrop={handleDrop} suppressHydrationWarning={suppressHydrationWarning || true}>
      <div className="w-full max-w-4xl mx-auto" suppressHydrationWarning={suppressHydrationWarning || true}>
        {isDragOver && <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center" suppressHydrationWarning={suppressHydrationWarning || true}><div className="bg-white dark:bg-gray-800 rounded-2xl p-8 shadow-2xl border-2 border-dashed border-teal-400" suppressHydrationWarning={suppressHydrationWarning || true}><Upload size={48} className="text-teal-500 mx-auto mb-4" /><h3 className="text-xl font-bold text-center mb-2">{t.dragDrop.title}</h3><p className="text-gray-600 dark:text-gray-400 text-center">{t.dragDrop.subtitle}</p></div></div>}
        {attachedFiles.length > 0 && <div className="mb-4 space-y-2" suppressHydrationWarning={suppressHydrationWarning || true}><div className="grid grid-cols-1 sm:grid-cols-2 gap-2" suppressHydrationWarning={suppressHydrationWarning || true}>{attachedFiles.map(file => <FilePreview key={file.id} file={file} onRemove={() => removeFile(file.id)} dictionary={dictionary} />)}</div></div>}
        <div className="flex items-end gap-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 focus-within:ring-2 focus-within:ring-amber-500 focus-within:border-amber-500 transition-all" suppressHydrationWarning={suppressHydrationWarning || true}>
          <textarea ref={textareaRef} value={inputMessage} onChange={(e) => setInputMessage(e.target.value)} onKeyPress={handleKeyPress} placeholder={t.input.placeholder} className="flex-1 bg-transparent border-none outline-none resize-none text-gray-900 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400 min-h-[20px] max-h-32" rows={1} dir="auto" />
          <div className="flex items-center gap-2" suppressHydrationWarning={suppressHydrationWarning || true}>
            <input ref={fileInputRef} type="file" multiple onChange={handleFileSelect} className="hidden" />
            <button onClick={() => fileInputRef.current?.click()} className="p-2 text-gray-500 hover:text-amber-600 transition-colors" title={t.input.attachFile}><Paperclip size={20} /></button>
            <button onClick={toggleRecording} className={`p-2 transition-colors ${isRecording ? 'text-red-500 animate-pulse' : 'text-gray-500 hover:text-amber-600'}`} title={isRecording ? t.input.stopRecording : t.input.startRecording}><Mic size={20} /></button>
            <button onClick={handleSendMessage} disabled={(!inputMessage.trim() && attachedFiles.length === 0) || isLoading} className="p-2 bg-amber-500 text-white rounded-xl hover:bg-amber-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"><Send size={20} /></button>
          </div>
        </div>
      </div>
    </div>
  );
};

// المكون الرئيسي
interface MainContentProps {
  messages: Message[];
  inputMessage: string;
  setInputMessage: (v: string) => void;
  attachedFiles: FileAttachment[];
  setAttachedFiles: (files: React.SetStateAction<FileAttachment[]>) => void;
  handleSendMessage: () => void;
  handleRegenerate: () => void;
  isLoading: boolean;
  toggleSidebar: () => void;
  dictionary: any;
}

const MainContent: React.FC<MainContentProps> = ({
  messages,
  inputMessage,
  setInputMessage,
  attachedFiles,
  setAttachedFiles,
  handleSendMessage,
  handleRegenerate,
  isLoading,
  toggleSidebar,
  dictionary
}) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const t = dictionary.mainContent;

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const lastMessage = messages[messages.length - 1];

  return (
    <div className="flex-1 flex flex-col h-screen bg-white dark:bg-gray-900" suppressHydrationWarning={true}>
      <header className="flex md:hidden items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900" suppressHydrationWarning={true}>
        <div className="flex items-center gap-3" suppressHydrationWarning={true}><SyrianEagle className="w-8 h-8" /><h1 className="font-bold text-lg text-gray-900 dark:text-gray-100">SyriaGPT</h1></div>
        <button onClick={toggleSidebar} className="p-2 text-gray-600 dark:text-gray-400 hover:text-amber-600 dark:hover:text-amber-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"><Menu size={24} /></button>
      </header>
      <div className="flex-1 overflow-y-auto" suppressHydrationWarning={true}>
        <div className="min-h-full flex flex-col" suppressHydrationWarning={true}>
          {messages.length === 0 ? (
            <WelcomeScreen onSuggestionClick={(suggestion) => setInputMessage(suggestion)} dictionary={dictionary} />
          ) : (
            <div className="flex-1 py-4 space-y-4" suppressHydrationWarning={true}>
              {messages.map(message => <MessageItem key={message.id} message={message} dictionary={dictionary} />)}
              {messages.length > 0 && lastMessage?.sender === 'bot' && !lastMessage?.isTyping && (
                <RegenerateResponse onRegenerate={handleRegenerate} dictionary={dictionary} />
              )}
              <div ref={messagesEndRef} suppressHydrationWarning={true} />
            </div>
          )}
        </div>
      </div>
      <ChatInputArea inputMessage={inputMessage} setInputMessage={setInputMessage} attachedFiles={attachedFiles} setAttachedFiles={setAttachedFiles} handleSendMessage={handleSendMessage} isLoading={isLoading} dictionary={dictionary} suppressHydrationWarning={true} />
      <div className="text-center text-xs text-gray-500 dark:text-gray-400 p-4 bg-gray-50 dark:bg-gray-800" suppressHydrationWarning={true}>{t.footer}</div>
    </div>
  );
};

export default MainContent;