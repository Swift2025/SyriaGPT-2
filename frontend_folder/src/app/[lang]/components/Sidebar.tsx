// src/app/[lang]/components/Sidebar.tsx
'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { usePathname, useRouter, useParams } from 'next/navigation';
import { 
  Plus, Sun, Moon, User, ChevronUp, LogOut, Star, Settings, 
  HelpCircle, Info, Languages, Menu, X, MessageSquare, 
  Sparkles, Clock, ChevronRight, Edit3, Trash2, Archive, MoreVertical,
  Search, Filter
} from 'lucide-react';
import { useAuth } from '../../../context/AuthContext';
import { getChats, createChat, deleteChat, updateChat, exportUserData } from '../../../../services/api';
import { Chat } from '../types';
import toast from 'react-hot-toast';

// واجهة لنوع بيانات المحادثة القادمة من الـ API
interface Conversation {
  id: string;
  title: string;
  last_message_at: string | null;
}

interface SidebarProps {
  darkMode: boolean;
  toggleDarkMode: () => void;
  isSidebarOpen: boolean;
  setIsSidebarOpen: (isOpen: boolean) => void;
  dictionary: any;
}

// مكون الهيكل العظمي للتحميل
const ConversationSkeleton = () => (
  <div className="p-3 rounded-xl bg-white/10 animate-pulse" suppressHydrationWarning={true}>
    <div className="flex items-center justify-between" suppressHydrationWarning={true}>
      <div className="flex-1 min-w-0 space-y-2" suppressHydrationWarning={true}>
        <div className="h-2 w-1/4 bg-white/20 rounded" suppressHydrationWarning={true}></div>
        <div className="h-3 w-3/4 bg-white/20 rounded" suppressHydrationWarning={true}></div>
      </div>
      <div className="h-4 w-4 bg-white/20 rounded-full" suppressHydrationWarning={true}></div>
    </div>
  </div>
);

const EnhancedSidebar: React.FC<SidebarProps> = ({ 
  darkMode, 
  toggleDarkMode, 
  isSidebarOpen, 
  setIsSidebarOpen,
  dictionary
}) => {
  const [isLogoutModalOpen, setIsLogoutModalOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [isLangMenuOpen, setIsLangMenuOpen] = useState(false);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [isLoadingChats, setIsLoadingChats] = useState(true);
  
  const langMenuRef = useRef<HTMLDivElement>(null);
  const userMenuRef = useRef<HTMLDivElement>(null);

  const router = useRouter();
  const pathname = usePathname();
  const params = useParams();
  const lang = params.lang as string;
  const t = dictionary.sidebar;

  const { user, logout, isLoading: isAuthLoading } = useAuth();
  
  // Debug: مراقبة حالة المستخدم
  useEffect(() => {
    console.log('Sidebar - User state changed:', { user, isAuthLoading });
    if (user) {
      console.log('Sidebar - User details:', {
        id: user.id,
        email: user.email,
        full_name: user.full_name,
        name: user.name
      });
    }
  }, [user, isAuthLoading]);

  useEffect(() => {
    const fetchConversations = async () => {
      if (user) {
        setIsLoadingChats(true);
        try {
          const userChats = await getChats();
          setConversations(userChats);
        } catch (error) {
          console.error("Failed to fetch conversations:", error);
        } finally {
          setIsLoadingChats(false);
        }
      } else if (!isAuthLoading) {
        setIsLoadingChats(false);
        setConversations([]);
      }
    };
    fetchConversations();
  }, [user, isAuthLoading]);

  const handleLanguageSelect = (newLang: string) => {
    if (newLang !== lang) {
      const newPath = pathname.replace(`/${lang}`, `/${newLang}`);
      window.location.href = newPath;
    }
    setIsLangMenuOpen(false);
  };

  const handleNewChat = async () => {
    if (!user) {
      toast.error("Please log in to start a new chat."); // يمكنك ترجمة هذه
      router.push(`/${lang}/login`);
      return;
    }
    try {
      const newChatData = await createChat({ title: t.newChat });
      // توجيه المستخدم إلى صفحة المحادثة الجديدة
      router.push(`/${lang}/chat/${newChatData.chat.id}`);
    } catch (error: any) {
      toast.error(error.message || "Failed to create a new chat.");
    }
  };

  const supportedLanguages = Object.keys(t.languageSelector.languages).map(key => ({
    code: key,
    name: t.languageSelector.languages[key].name,
    country: t.languageSelector.languages[key].country
  }));
  const currentLanguage = supportedLanguages.find(l => l.code === lang);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (langMenuRef.current && !langMenuRef.current.contains(event.target as Node)) setIsLangMenuOpen(false);
      if (userMenuRef.current && !userMenuRef.current.contains(event.target as Node)) setUserMenuOpen(false);
      const sidebar = document.getElementById('sidebar');
      const toggleButton = document.getElementById('sidebar-toggle');
      if (isSidebarOpen && sidebar && !sidebar.contains(event.target as Node) && toggleButton && !toggleButton.contains(event.target as Node) && window.innerWidth < 768) setIsSidebarOpen(false);
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isSidebarOpen, setIsSidebarOpen]);

  const handleLogout = () => {
    setIsLogoutModalOpen(false);
    logout();
  };

  return (
    <>
      <button id="sidebar-toggle" onClick={() => setIsSidebarOpen(!isSidebarOpen)} className={`fixed top-4 left-4 z-50 md:hidden w-12 h-12 rounded-xl ${darkMode ? 'bg-gray-800 hover:bg-gray-700' : 'bg-white hover:bg-gray-50'} shadow-lg border transition-all duration-300 flex items-center justify-center ${isSidebarOpen ? 'rotate-180' : 'rotate-0'}`}>
        {isSidebarOpen ? <X size={20} className={darkMode ? 'text-white' : 'text-gray-700'} /> : <Menu size={20} className={darkMode ? 'text-white' : 'text-gray-700'} />}
      </button>

      {isSidebarOpen && <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-30 md:hidden transition-opacity duration-300" onClick={() => setIsSidebarOpen(false)} />}
      
      <aside id="sidebar" className={`fixed top-0 right-0 h-full w-80 z-40 transform transition-all duration-300 ease-in-out md:relative md:translate-x-0 md:w-64 ${isSidebarOpen ? 'translate-x-0' : 'translate-x-full'} ${darkMode ? 'bg-gradient-to-b from-gray-900 to-gray-800 border-l border-gray-700' : 'bg-gradient-to-b from-teal-600 via-teal-700 to-teal-800 border-l border-teal-600'} text-white flex flex-col shadow-2xl backdrop-blur-xl`} suppressHydrationWarning={true}>
        <div className="p-6 border-b border-white/10" suppressHydrationWarning={true}>
          <div className="flex items-center justify-center mb-6" suppressHydrationWarning={true}>
            <div className="w-12 h-12 rounded-full bg-gradient-to-r from-amber-700 to-amber-600 flex items-center justify-center shadow-lg" suppressHydrationWarning={true}><Sparkles size={24} className="text-white" /></div>
            <div className="mr-3 text-right" suppressHydrationWarning={true}><h1 className="font-bold text-lg">Syria GPT</h1><p className="text-xs text-white/70">{t.tagline}</p></div>
          </div>
          <button onClick={handleNewChat} className="w-full flex items-center justify-center gap-3 p-4 rounded-xl bg-gradient-to-r from-amber-700 to-amber-600 hover:from-amber-600 hover:to-amber-700 transition-all duration-300 shadow-lg hover:shadow-xl transform hover:scale-105 group" suppressHydrationWarning={true}><Plus size={20} className="group-hover:rotate-90 transition-transform duration-300" /><span className="font-semibold">{t.newChat}</span></button>
        </div>
      
        <div className="flex-1 p-4 overflow-y-auto custom-scrollbar" suppressHydrationWarning={true}>
          <div className="mb-4" suppressHydrationWarning={true}>
            <div className="flex items-center gap-2 text-sm text-white/60 mb-3" suppressHydrationWarning={true}><Clock size={16} /><span>{t.pastConversations}</span></div>
            <div className="space-y-2" suppressHydrationWarning={true}>
              {isLoadingChats ? (
                <><ConversationSkeleton /><ConversationSkeleton /><ConversationSkeleton /></>
              ) : conversations.length > 0 ? (
                conversations.map((conversation) => (
                  <Link href={`/${lang}/chat/${conversation.id}`} key={conversation.id} className="block group relative p-3 rounded-xl transition-all duration-300 cursor-pointer hover:bg-white/10" suppressHydrationWarning={true}>
                    <div className="flex items-center justify-between" suppressHydrationWarning={true}>
                      <div className="flex-1 min-w-0" suppressHydrationWarning={true}><h3 className="text-sm font-medium text-white truncate">{conversation.title || 'Untitled Chat'}</h3></div>
                      <ChevronRight size={16} className="text-white/40 transition-transform duration-300 group-hover:translate-x-1" />
                    </div>
                  </Link>
                ))
              ) : (
                <div className="text-center text-xs text-white/50 p-4" suppressHydrationWarning={true}>No past conversations. Start a new one!</div>
              )}
            </div>
          </div>
        </div>
      
        <div className="p-4 space-y-3 border-t border-white/10 bg-black/20 backdrop-blur-sm" suppressHydrationWarning={true}>
          <button onClick={toggleDarkMode} className="w-full flex items-center gap-3 p-3 rounded-xl hover:bg-white/10 transition-all duration-300 group" suppressHydrationWarning={true}>
            <div className={`p-2 rounded-lg ${darkMode ? 'bg-yellow-500/20' : 'bg-blue-500/20'} group-hover:scale-110 transition-transform duration-300`} suppressHydrationWarning={true}>{darkMode ? <Sun size={18} className="text-yellow-400" /> : <Moon size={18} className="text-blue-400" />}</div>
            <span className="text-sm font-medium">{darkMode ? t.lightMode : t.darkMode}</span>
          </button>

          <div className="relative" ref={langMenuRef} suppressHydrationWarning={true}>
            <button onClick={() => setIsLangMenuOpen(!isLangMenuOpen)} className="w-full flex items-center justify-between gap-3 p-3 rounded-xl hover:bg-white/10 transition-all duration-300 group" suppressHydrationWarning={true}>
              <div className="flex items-center gap-3" suppressHydrationWarning={true}>
                <div className="p-2 rounded-lg bg-green-500/20 group-hover:scale-110 transition-transform duration-300" suppressHydrationWarning={true}><Languages size={18} className="text-green-400" /></div>
                <span className="text-sm font-medium">{currentLanguage?.name || t.languageSelector.title}</span>
              </div>
              <ChevronUp size={16} className={`transition-transform duration-300 ${isLangMenuOpen ? 'rotate-0' : 'rotate-180'}`} />
            </button>
            {isLangMenuOpen && (
              <div className="absolute bottom-full right-0 mb-2 w-full rounded-xl bg-gray-900/95 backdrop-blur-xl shadow-2xl border border-white/10 overflow-hidden animate-in fade-in duration-200" suppressHydrationWarning={true}>
                <div className="p-2 space-y-1 max-h-60 overflow-y-auto custom-scrollbar" suppressHydrationWarning={true}>
                  {supportedLanguages.map((language) => (
                    <button key={language.code} onClick={() => handleLanguageSelect(language.code)} className={`w-full text-right flex items-center gap-3 p-3 rounded-lg transition-colors ${lang === language.code ? 'bg-white/20' : 'hover:bg-white/10'}`} suppressHydrationWarning={true}>
                      <Image src={`https://flagsapi.com/${language.country}/shiny/64.png`} alt={`${language.name} flag`} width={24} height={24} className="w-6 h-6 rounded-full object-cover" />
                      <span className="text-sm font-medium">{language.name}</span>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="p-4 border-t border-white/10 bg-black/30 backdrop-blur-sm mt-auto" suppressHydrationWarning={true}>
          {isAuthLoading ? (
            <div className="h-[56px] flex items-center justify-center" suppressHydrationWarning={true}><div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" suppressHydrationWarning={true}></div></div>
          ) : user ? (
            <div className="relative" ref={userMenuRef} suppressHydrationWarning={true}>
              <button onClick={() => setUserMenuOpen(!userMenuOpen)} className="w-full flex items-center justify-between p-3 rounded-xl hover:bg-white/10 transition-all duration-300 group" suppressHydrationWarning={true}>
                <div className="flex items-center gap-3" suppressHydrationWarning={true}>
                  <div className="w-10 h-10 rounded-full bg-gradient-to-r from-blue-500 to-purple-600 flex items-center justify-center shadow-lg" suppressHydrationWarning={true}><User size={20} /></div>
                  <div className="text-right" suppressHydrationWarning={true}><p className="text-sm font-semibold">{user.full_name || user.name || 'User'}</p><p className="text-xs text-white/60">{user.email}</p></div>
                </div>
                <ChevronUp className={`transform transition-transform duration-300 ${userMenuOpen ? 'rotate-0' : 'rotate-180'}`} size={18} />
              </button>
              {userMenuOpen && (
                <div className="absolute bottom-full right-0 mb-2 w-full rounded-xl bg-gray-900/95 backdrop-blur-xl shadow-2xl border border-white/10 overflow-hidden" suppressHydrationWarning={true}>
                  <div className="p-2 space-y-1" suppressHydrationWarning={true}>
                    <Link href={`/${lang}/profile`} className="flex items-center gap-3 p-3 rounded-lg hover:bg-white/10 transition-colors group" suppressHydrationWarning={true}><User className="text-blue-400" size={18} /><span className="text-sm">{t.profile}</span></Link>
                    <Link href={`/${lang}/settings`} className="flex items-center gap-3 p-3 rounded-lg hover:bg-white/10 transition-colors group" suppressHydrationWarning={true}><Settings className="text-gray-400" size={18} /><span className="text-sm">{t.settings}</span></Link>
                    <Link href={`/${lang}/upgrade`} className="flex items-center gap-3 p-3 rounded-lg hover:bg-white/10 transition-colors group" suppressHydrationWarning={true}><Star className="text-yellow-400" size={18} /><span className="text-sm">{t.upgradeToPro}</span><span className="mr-auto text-xs bg-yellow-500/20 text-yellow-400 px-2 py-1 rounded-full">{t.newBadge}</span></Link>
                    <div className="h-px bg-white/10 my-2" suppressHydrationWarning={true}></div>
                    <button onClick={() => setIsLogoutModalOpen(true)} className="w-full flex items-center gap-3 p-3 rounded-lg hover:bg-red-500/10 transition-colors group text-red-400" suppressHydrationWarning={true}><LogOut size={18} /><span className="text-sm">{t.logout}</span></button>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="space-y-3" suppressHydrationWarning={true}>
              <Link href={`/${lang}/login`} className="block w-full text-center px-4 py-3 bg-gradient-to-r from-amber-500 to-green-500 text-white font-semibold rounded-xl shadow-lg hover:scale-105 transition-transform" suppressHydrationWarning={true}>تسجيل الدخول</Link>
              <Link href={`/${lang}/register`} className="block w-full text-center px-4 py-3 bg-white/10 text-white font-semibold rounded-xl hover:bg-white/20 transition-colors" suppressHydrationWarning={true}>إنشاء حساب</Link>
            </div>
          )}
        </div>
      </aside>

      {isLogoutModalOpen && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4" suppressHydrationWarning={true}>
          <div className={`max-w-md w-full rounded-2xl p-6 shadow-2xl ${darkMode ? 'bg-gray-800' : 'bg-white'}`} suppressHydrationWarning={true}>
            <div className="text-center" suppressHydrationWarning={true}>
              <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4" suppressHydrationWarning={true}><LogOut className="text-red-600" size={32} /></div>
              <h3 className={`text-lg font-bold mb-2 ${darkMode ? 'text-white' : 'text-gray-900'}`}>{t.logoutModal.title}</h3>
              <p className={`mb-6 ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>{t.logoutModal.description}</p>
              <div className="flex gap-3" suppressHydrationWarning={true}>
                <button onClick={() => setIsLogoutModalOpen(false)} className={`flex-1 px-4 py-2 rounded-lg border transition-colors ${darkMode ? 'border-gray-600 text-gray-300 hover:bg-gray-700' : 'border-gray-300 text-gray-700 hover:bg-gray-50'}`} suppressHydrationWarning={true}>{t.logoutModal.cancel}</button>
                <button onClick={handleLogout} className="flex-1 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors" suppressHydrationWarning={true}>{t.logoutModal.confirm}</button>
              </div>
            </div>
          </div>
        </div>
      )}

      <style jsx suppressHydrationWarning={true}>{`
        .custom-scrollbar::-webkit-scrollbar { width: 6px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: rgba(255, 255, 255, 0.1); border-radius: 3px; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.2); border-radius: 3px; }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: rgba(255, 255, 255, 0.3); }
        .animate-in { animation: fadeIn 0.2s ease-out; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
      `}</style>
    </>
  );
};

export default EnhancedSidebar;