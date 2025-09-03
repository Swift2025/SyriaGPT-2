// src/app/[lang]/not-found.tsx
'use client';

import React, { useState, useEffect } from 'react';
import { 
  Home, 
  Search, 
  ArrowLeft, 
  Map,
  Compass,
  MapPin,
  HelpCircle,
  MessageCircle,
  ChevronRight,
  History,
  Sparkles,
  Navigation,
  Globe,
  BookOpen,
  Coffee,
  RefreshCw
} from 'lucide-react';
import Link from 'next/link';
import { useRouter, useParams } from 'next/navigation';
import { getDictionary } from '../../../get-dictionary';
import { Locale } from '../../../i18n-config';

// مكون النسر السوري الضائع
const LostSyrianEagle: React.FC<{ className?: string }> = ({ className = "w-32 h-32" }) => {
  const [eyePosition, setEyePosition] = useState({ x: 0, y: 0 });

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      const x = (e.clientX / window.innerWidth - 0.5) * 10;
      const y = (e.clientY / window.innerHeight - 0.5) * 10;
      setEyePosition({ x, y });
    };

    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  return (
    <div className={`${className} relative`}>
      <svg viewBox="0 0 200 200" className="w-full h-full">
        <g transform="translate(100, 100)">
          <ellipse cx="0" cy="10" rx="25" ry="35" fill="#B9A779" opacity="0.8" />
          <path d="M -60 0 Q -40 -20, -25 -10 L -25 10 Q -40 20, -60 30 Z" fill="#B9A779" opacity="0.8" />
          <path d="M 60 0 Q 40 -20, 25 -10 L 25 10 Q 40 20, 60 30 Z" fill="#B9A779" opacity="0.8" />
          <circle cx="0" cy="-15" r="15" fill="#B9A779" />
          <path d="M 0 -15 L 5 -10 L 0 -5 L -5 -10 Z" fill="#8B7F5C" />
          <g>
            <circle cx="-5" cy="-15" r="4" fill="white" />
            <circle cx={-5 + eyePosition.x * 0.2} cy={-15 + eyePosition.y * 0.2} r="2" fill="#2C2416" />
            <circle cx="5" cy="-15" r="4" fill="white" />
            <circle cx={5 + eyePosition.x * 0.2} cy={-15 + eyePosition.y * 0.2} r="2" fill="#2C2416" />
          </g>
          <text x="0" y="-40" fontSize="24" fill="#428177" textAnchor="middle" className="animate-bounce">؟</text>
        </g>
      </svg>
    </div>
  );
};

// مكون البوصلة المتحركة
const AnimatedCompass: React.FC = () => {
  const [rotation, setRotation] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setRotation(prev => (prev + 1) % 360);
    }, 50);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="relative w-24 h-24">
      <Compass 
        className="w-full h-full text-[#428177] opacity-20" 
        style={{ transform: `rotate(${rotation}deg)` }}
      />
    </div>
  );
};

export default function NotFoundPage() {
  const router = useRouter();
  const params = useParams();
  const [dictionary, setDictionary] = useState<any>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [visitedPages, setVisitedPages] = useState<string[]>([]);
  const [showFunFact, setShowFunFact] = useState(false);

  const lang = (params.lang || 'ar') as Locale;

  useEffect(() => {
    const fetchDictionary = async () => {
      try {
        const dict = await getDictionary(lang);
        setDictionary(dict);
      } catch (e) {
        console.error("Failed to load dictionary for not-found page:", e);
      }
    };
    fetchDictionary();
  }, [lang]);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const mockHistory = ['/profile', '/settings'];
      setVisitedPages(mockHistory.slice(0, 3));
    }
    const timer = setTimeout(() => setShowFunFact(true), 3000);
    return () => clearTimeout(timer);
  }, []);

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    setIsSearching(true);
    await new Promise(resolve => setTimeout(resolve, 1000));
    router.push(`/${lang}/?search=${encodeURIComponent(searchQuery)}`);
  };

  if (!dictionary) {
    return <div className="min-h-screen flex items-center justify-center bg-gray-100 dark:bg-gray-900">Loading...</div>;
  }

  const t = dictionary.notFoundPage;
  const randomFact = t.funFact.facts[Math.floor(Math.random() * t.funFact.facts.length)];
  const suggestedPages = [
    { icon: <Home className="w-5 h-5" />, href: `/${lang}`, ...t.suggestions.items[0] },
    { icon: <MessageCircle className="w-5 h-5" />, href: `/${lang}`, ...t.suggestions.items[1] },
    { icon: <BookOpen className="w-5 h-5" />, href: `/${lang}/help`, ...t.suggestions.items[2] },
    { icon: <Globe className="w-5 h-5" />, href: `/${lang}/about`, ...t.suggestions.items[3] }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#D9D9D9] via-gray-100 to-[#D9D9D9] dark:from-[#002326] dark:via-[#054239] dark:to-[#002326] overflow-hidden">
      <div className="absolute inset-0">
        <div className="absolute inset-0 opacity-5 dark:opacity-10">
          <div className="grid grid-cols-12 gap-4 p-8 transform rotate-12 scale-110">
            {Array.from({ length: 48 }).map((_, i) => <MapPin key={i} className="w-8 h-8 text-[#428177]" />)}
          </div>
        </div>
        <div className="absolute top-20 left-20" style={{ animation: 'float 4s ease-in-out infinite' }}><AnimatedCompass /></div>
        <div className="absolute bottom-20 right-20" style={{ animation: 'float 4s ease-in-out 1s infinite' }}><Map className="w-32 h-32 text-[#B9A779] opacity-10" /></div>
      </div>

      <div className="relative z-10 flex flex-col items-center justify-center min-h-screen px-4 py-12">
        <div className="w-full max-w-4xl">
          <div className="text-center mb-8">
            <LostSyrianEagle className="w-32 h-32 mx-auto mb-6" />
            <div className="relative mb-6">
              <h1 className="text-[120px] md:text-[160px] font-bold text-[#428177]/20 dark:text-[#B9A779]/20 leading-none">404</h1>
              <div className="absolute inset-0 flex items-center justify-center"><Navigation className="w-16 h-16 text-[#428177] dark:text-[#B9A779]" style={{ animation: 'spin 20s linear infinite' }} /></div>
            </div>
            <h2 className="text-3xl md:text-4xl font-bold text-[#054239] dark:text-[#B9A779] mb-4">{t.title}</h2>
            <p className="text-lg text-gray-600 dark:text-gray-400 mb-2">{t.description}</p>
            <p className="text-sm text-gray-500 dark:text-gray-500 flex items-center justify-center gap-2"><MapPin className="w-4 h-4" />{t.currentLocation}</p>
          </div>

          <div className="bg-white/80 dark:bg-[#161616]/80 backdrop-blur-lg rounded-2xl shadow-xl p-6 mb-6">
            <div className="relative">
              <div className="flex items-center gap-3 bg-gray-100 dark:bg-gray-800 rounded-xl p-3">
                <Search className="w-5 h-5 text-gray-400" />
                <input type="text" value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} onKeyPress={(e) => e.key === 'Enter' && handleSearch()} placeholder={t.search.placeholder} className="flex-1 bg-transparent outline-none text-gray-700 dark:text-gray-300 placeholder-gray-500" dir="auto" />
                <button onClick={handleSearch} disabled={isSearching} className="px-4 py-2 bg-[#428177] text-white rounded-lg hover:bg-[#054239] transition-colors disabled:opacity-50">{isSearching ? <RefreshCw className="w-4 h-4 animate-spin" /> : t.search.button}</button>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            <button onClick={() => router.back()} className="bg-white/80 dark:bg-[#161616]/80 backdrop-blur-lg rounded-xl p-4 hover:shadow-lg transition-all group">
              <div className="flex items-center gap-3"><div className="p-3 bg-gray-100 dark:bg-gray-800 rounded-lg group-hover:bg-[#428177]/20 transition-colors"><ArrowLeft className="w-6 h-6 text-[#428177]" /></div><div className="text-right"><h3 className="font-semibold text-gray-800 dark:text-gray-200">{t.actions.previousPage.title}</h3><p className="text-sm text-gray-500 dark:text-gray-400">{t.actions.previousPage.description}</p></div></div>
            </button>
            <Link href={`/${lang}`} className="bg-white/80 dark:bg-[#161616]/80 backdrop-blur-lg rounded-xl p-4 hover:shadow-lg transition-all group">
              <div className="flex items-center gap-3"><div className="p-3 bg-gray-100 dark:bg-gray-800 rounded-lg group-hover:bg-[#B9A779]/20 transition-colors"><Home className="w-6 h-6 text-[#B9A779]" /></div><div className="text-right"><h3 className="font-semibold text-gray-800 dark:text-gray-200">{t.actions.homePage.title}</h3><p className="text-sm text-gray-500 dark:text-gray-400">{t.actions.homePage.description}</p></div></div>
            </Link>
          </div>

          <div className="bg-white/80 dark:bg-[#161616]/80 backdrop-blur-lg rounded-2xl shadow-xl p-6 mb-6">
            <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-4 flex items-center gap-2"><Sparkles className="w-5 h-5 text-[#428177]" />{t.suggestions.title}</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {suggestedPages.map((page, index) => <Link key={index} href={page.href} className="flex items-center gap-3 p-3 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors cursor-pointer group"><div className="text-[#428177]">{page.icon}</div><div className="flex-1"><h4 className="font-medium text-gray-800 dark:text-gray-200 group-hover:text-[#428177] transition-colors">{page.title}</h4><p className="text-xs text-gray-500 dark:text-gray-400">{page.description}</p></div><ChevronRight className="w-4 h-4 text-gray-400 group-hover:text-[#428177] transition-colors" /></Link>)}
            </div>
          </div>

          {visitedPages.length > 0 && <div className="bg-white/80 dark:bg-[#161616]/80 backdrop-blur-lg rounded-2xl shadow-xl p-6 mb-6"><h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-4 flex items-center gap-2"><History className="w-5 h-5 text-[#B9A779]" />{t.history.title}</h3><div className="flex flex-wrap gap-2">{visitedPages.map((page, index) => <Link key={index} href={`/${lang}${page}`} className="px-3 py-1 bg-gray-100 dark:bg-gray-800 rounded-full text-sm text-gray-700 dark:text-gray-300 hover:bg-[#428177]/20 transition-colors cursor-pointer">{page}</Link>)}</div></div>}
          {showFunFact && <div className="bg-gradient-to-r from-[#428177]/10 to-[#B9A779]/10 backdrop-blur-lg rounded-2xl p-6" style={{ animation: 'fadeIn 0.5s ease-out' }}><div className="flex items-start gap-3"><Coffee className="w-6 h-6 text-[#B9A779] mt-1" /><div><h4 className="font-semibold text-gray-800 dark:text-gray-200 mb-1">{t.funFact.title}</h4><p className="text-gray-600 dark:text-gray-400">{randomFact}</p></div></div></div>}
          <div className="text-center mt-8">
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-3">{t.support.message}</p>
            <div className="flex items-center justify-center gap-4">
              <Link href={`/${lang}/help`} className="flex items-center gap-1 text-[#428177] hover:underline text-sm"><HelpCircle className="w-4 h-4" />{t.support.helpCenter}</Link>
              <span className="text-gray-400">•</span>
              <a href="mailto:support@syriagpt.com" className="flex items-center gap-1 text-[#428177] hover:underline text-sm"><MessageCircle className="w-4 h-4" />{t.support.technicalSupport}</a>
            </div>
          </div>
        </div>
      </div>

      <style jsx>{`
        @keyframes float { 0%, 100% { transform: translateY(0px); } 50% { transform: translateY(-20px); } }
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
      `}</style>
    </div>
  );
};