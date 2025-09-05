// src/app/[lang]/upgrade/UpgradePageClient.tsx
'use client';

import React, { useState } from 'react';
import { CheckCircle, XCircle, Star, Zap, Shield, ChevronDown, Crown, Rocket, Clock, Heart, Gift, Users } from 'lucide-react';

// مكون شعار النسر السوري
const SyrianEagle: React.FC<{ className?: string }> = ({ className = "w-16 h-16" }) => (
  <div className={`${className} flex items-center justify-center`}>
    <img src="/images/logo.ai.svg" alt="Syrian Eagle Logo" className="w-full h-full drop-shadow-lg" />
  </div>
);

// مكون ميزة في جدول المقارنة
const FeatureRow: React.FC<{ 
  text: string; 
  free: boolean; 
  pro: boolean;
  icon?: React.ReactNode;
  highlight?: boolean;
}> = ({ text, free, pro, icon, highlight = false }) => (
  <div className={`flex items-center justify-between py-4 px-4 rounded-lg transition-all duration-300 ${
    highlight ? 'bg-gradient-to-r from-amber-50 to-green-50 dark:from-amber-900/20 dark:to-green-900/20 border border-amber-200 dark:border-amber-700/30' : 'hover:bg-gray-50 dark:hover:bg-gray-700/50'
  }`}>
    <div className="flex items-center gap-3">
      {icon && <span className="text-amber-600 dark:text-amber-400">{icon}</span>}
      <span className="text-gray-800 dark:text-gray-200 font-medium">{text}</span>
    </div>
    <div className="flex items-center gap-12">
      <div className="w-8 text-center">
        {free ? <CheckCircle className="text-green-500 mx-auto" size={20} /> : <XCircle className="text-gray-400 mx-auto" size={20} />}
      </div>
      <div className="w-8 text-center">
        {pro ? <CheckCircle className="text-amber-600 dark:text-amber-400 mx-auto" size={20} /> : <XCircle className="text-gray-400 mx-auto" size={20} />}
      </div>
    </div>
  </div>
);

// مكون سؤال الأكورديون
const FaqItem: React.FC<{ 
  question: string; 
  children: React.ReactNode;
  dictionary: any;
}> = ({ question, children, dictionary }) => {
  const [isOpen, setIsOpen] = useState(false);
  const t = dictionary.upgradePage.faq;
  
  return (
    <div className="border-b border-amber-100 dark:border-gray-700 last:border-b-0 hover:bg-gradient-to-r hover:from-amber-50/50 hover:to-green-50/30 dark:hover:from-gray-800/30 dark:hover:to-gray-700/30 transition-all duration-300 rounded-lg">
      <button onClick={() => setIsOpen(!isOpen)} className="w-full flex justify-between items-center text-right py-6 px-4 group focus:outline-none focus:ring-2 focus:ring-amber-400 focus:ring-opacity-50 rounded-lg">
        <span className="font-bold text-lg text-gray-800 dark:text-gray-100 group-hover:text-amber-800 dark:group-hover:text-amber-200 transition-colors duration-300 pr-4">{question}</span>
        <div className="flex items-center gap-3">
          <span className="text-sm text-amber-600 dark:text-amber-400 font-medium opacity-0 group-hover:opacity-100 transition-opacity duration-300">{isOpen ? t.toggleClose : t.toggleOpen}</span>
          <ChevronDown className={`transform transition-all duration-500 text-amber-600 dark:text-amber-400 group-hover:scale-110 ${isOpen ? 'rotate-180' : 'rotate-0'}`} size={24} />
        </div>
      </button>
      <div className={`overflow-hidden transition-all duration-500 ease-out ${isOpen ? 'max-h-96 opacity-100' : 'max-h-0 opacity-0'}`}>
        <div className="pb-6 px-4 text-gray-700 dark:text-gray-300 leading-relaxed bg-gradient-to-r from-amber-50/30 to-transparent dark:from-gray-800/20 dark:to-transparent rounded-lg">
          <div className="border-r-4 border-amber-300 dark:border-amber-600 pr-4">{children}</div>
        </div>
      </div>
    </div>
  );
};

// مكون بطاقة خطة التسعير
const PricingCard: React.FC<{
  title: string;
  subtitle: string;
  price: string;
  period: string;
  isPopular?: boolean;
  popularText: string;
  features: string[];
  buttonText: string;
  buttonAction: () => void;
  isDisabled?: boolean;
}> = ({ title, subtitle, price, period, isPopular = false, popularText, features, buttonText, buttonAction, isDisabled = false }) => (
  <div className={`relative rounded-3xl p-8 transition-all duration-300 hover:scale-105 hover:shadow-2xl ${isPopular ? 'bg-gradient-to-br from-amber-100 via-green-100 to-yellow-100 dark:from-amber-900/30 dark:via-green-900/30 dark:to-yellow-900/30 border-2 border-amber-400 dark:border-amber-600 shadow-2xl' : 'bg-white/90 dark:bg-gray-800/90 border border-gray-200 dark:border-gray-700 shadow-lg'} backdrop-blur-xl`}>
    {isPopular && <div className="absolute -top-4 right-6 bg-gradient-to-r from-amber-500 to-green-500 text-white px-4 py-2 rounded-full text-sm font-bold shadow-lg animate-pulse">{popularText}</div>}
    <div className="text-center mb-8">
      <div className={`w-16 h-16 mx-auto mb-4 rounded-2xl flex items-center justify-center shadow-lg ${isPopular ? 'bg-gradient-to-r from-amber-500 to-green-500' : 'bg-gradient-to-r from-gray-400 to-gray-500'}`}>{isPopular ? <Crown size={32} className="text-white" /> : <Users size={32} className="text-white" />}</div>
      <h3 className="text-2xl font-bold text-gray-800 dark:text-gray-100 mb-2">{title}</h3>
      <p className="text-gray-600 dark:text-gray-400 mb-6">{subtitle}</p>
      <div className="mb-6"><span className="text-5xl font-bold text-gray-800 dark:text-gray-100">{price}</span><span className="text-lg font-medium text-gray-600 dark:text-gray-400 mr-2">/ {period}</span></div>
    </div>
    <ul className="space-y-3 mb-8">{features.map((feature, index) => <li key={index} className="flex items-center gap-3"><CheckCircle size={20} className={isPopular ? 'text-amber-600 dark:text-amber-400' : 'text-green-500'} /><span className="text-gray-700 dark:text-gray-300">{feature}</span></li>)}</ul>
    <button onClick={buttonAction} disabled={isDisabled} className={`w-full py-4 px-6 rounded-2xl font-bold text-lg transition-all duration-300 transform ${isDisabled ? 'bg-gray-200 dark:bg-gray-700 text-gray-500 dark:text-gray-400 cursor-not-allowed' : isPopular ? 'bg-gradient-to-r from-amber-500 to-green-500 hover:from-amber-600 hover:to-green-600 text-white shadow-lg hover:shadow-xl hover:scale-105 active:scale-95' : 'bg-gradient-to-r from-gray-600 to-gray-700 hover:from-gray-700 hover:to-gray-800 text-white shadow-lg hover:shadow-xl hover:scale-105 active:scale-95'}`}>{buttonText}</button>
  </div>
);

export default function UpgradePageClient({ dictionary }: { dictionary: any }) {
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'yearly'>('monthly');
  const t = dictionary.upgradePage;

  const handleUpgrade = () => {
    alert(t.alert);
  };

  return (
    <main className="flex-1 overflow-y-auto bg-gradient-to-br from-amber-50 via-green-50 to-yellow-50 dark:from-gray-900 dark:via-gray-900 dark:to-gray-800 font-arabic min-h-screen">
      <div className="fixed inset-0 opacity-30 dark:opacity-10 -z-10"><div className="absolute top-0 left-0 w-72 h-72 bg-amber-300 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-blob"></div><div className="absolute top-0 right-0 w-72 h-72 bg-green-300 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-blob animation-delay-2000"></div><div className="absolute bottom-0 left-1/2 w-72 h-72 bg-yellow-300 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-blob animation-delay-4000"></div></div>
      <div className="relative z-10 max-w-7xl mx-auto px-4 py-12 md:py-20">
        <header className="text-center mb-16">
          <div className="inline-flex items-center gap-3 mb-6"><SyrianEagle className="w-16 h-16 animate-float" /></div>
          <h1 className="text-5xl md:text-6xl font-bold bg-gradient-to-r from-amber-800 via-green-700 to-amber-900 bg-clip-text text-transparent mb-6">{t.header.title}</h1>
          <p className="text-xl text-gray-700 dark:text-gray-300 max-w-3xl mx-auto leading-relaxed mb-8">{t.header.description}</p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-2xl mx-auto">
            {t.stats.map((stat: { value: string; label: string }, index: number) => <div key={index} className="text-center"><div className="text-3xl font-bold text-amber-600 dark:text-amber-400">{stat.value}</div><div className="text-sm text-gray-600 dark:text-gray-400">{stat.label}</div></div>)}
          </div>
        </header>
        <div className="flex justify-center items-center gap-6 mb-16">
          <div className="bg-white/90 dark:bg-gray-800/90 backdrop-blur-xl rounded-2xl p-2 shadow-lg border border-amber-200/50 dark:border-amber-700/30">
            <div className="flex items-center gap-4 px-4">
              <span className={`font-semibold transition-colors duration-300 ${billingCycle === 'monthly' ? 'text-amber-600 dark:text-amber-400' : 'text-gray-500 dark:text-gray-400'}`}>{t.billingToggle.monthly}</span>
              <button onClick={() => setBillingCycle(billingCycle === 'monthly' ? 'yearly' : 'monthly')} className={`relative inline-flex h-8 w-14 items-center rounded-full transition-all duration-300 shadow-lg ${billingCycle === 'yearly' ? 'bg-gradient-to-r from-amber-500 to-green-500' : 'bg-gray-300 dark:bg-gray-600'}`}><span className={`inline-block h-6 w-6 transform rounded-full bg-white transition-transform duration-300 shadow-md ${billingCycle === 'yearly' ? 'translate-x-7' : 'translate-x-1'}`} /></button>
              <span className={`font-semibold transition-colors duration-300 ${billingCycle === 'yearly' ? 'text-amber-600 dark:text-amber-400' : 'text-gray-500 dark:text-gray-400'}`}>{t.billingToggle.yearly}</span>
              {billingCycle === 'yearly' && <div className="flex items-center gap-2 bg-gradient-to-r from-green-500 to-emerald-500 text-white px-3 py-1 rounded-full text-sm font-bold animate-pulse"><Gift size={14} />{t.billingToggle.saving}</div>}
            </div>
          </div>
        </div>
        <section className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-20 max-w-5xl mx-auto">
          <PricingCard {...t.pricingCards.free} buttonAction={() => {}} isDisabled={true} popularText="" />
          <PricingCard {...t.pricingCards.pro} price={billingCycle === 'monthly' ? t.pricingCards.pro.priceMonthly : t.pricingCards.pro.priceYearly} period={billingCycle === 'monthly' ? t.pricingCards.pro.periodMonthly : t.pricingCards.pro.periodYearly} buttonAction={handleUpgrade} isPopular={true} popularText={t.pricingCards.pro.popular} />
        </section>
        <section className="mb-20">
          <h2 className="text-4xl font-bold text-center mb-12 text-gray-800 dark:text-gray-100">{t.comparison.title}</h2>
          <div className="bg-white/60 dark:bg-gray-800/40 backdrop-blur-sm rounded-3xl shadow-2xl p-8 border border-amber-200/50 dark:border-amber-700/30">
            <div className="flex justify-between items-center mb-8"><h3 className="font-bold text-2xl text-gray-800 dark:text-gray-100">{t.comparison.featureHeader}</h3><div className="flex items-center gap-12"><span className="w-20 text-center font-bold text-lg text-gray-600 dark:text-gray-400">{t.comparison.freeHeader}</span><span className="w-20 text-center font-bold text-lg text-amber-600 dark:text-amber-400">{t.comparison.proHeader}</span></div></div>
            <div className="space-y-2">{t.comparison.features.map((feature: { text: string; free: boolean; pro: boolean }, index: number) => <FeatureRow key={index} {...feature} icon={[<Zap/>, <Clock/>, <Rocket/>, <Crown/>, <Clock/>, <Zap/>, <Star/>, <Shield/>, <Heart/>][index]} highlight={!feature.free && feature.pro} />)}</div>
          </div>
        </section>
        <section className="mb-16">
          <h2 className="text-4xl font-bold text-center mb-12 text-gray-800 dark:text-gray-100">{t.faq.title}</h2>
          <div className="bg-white/60 dark:bg-gray-800/40 backdrop-blur-sm rounded-3xl shadow-2xl p-8 border border-amber-200/50 dark:border-amber-700/30 max-w-4xl mx-auto">
            <div className="space-y-2">{t.faq.items.map((faq: { question: string; answer: string }, index: number) => <FaqItem key={index} question={faq.question} index={index} dictionary={dictionary}><p className="text-base leading-relaxed">{faq.answer}</p></FaqItem>)}</div>
          </div>
        </section>
        <section className="text-center">
          <div className="bg-gradient-to-br from-amber-600 via-green-600 to-amber-700 rounded-3xl p-12 shadow-2xl relative overflow-hidden">
            <div className="absolute inset-0 opacity-20"><svg width="60" height="60" viewBox="0 0 60 60" xmlns="http://www.w3.org/2000/svg" className="w-full h-full"><defs><pattern id="upgrade-dots" x="0" y="0" width="60" height="60" patternUnits="userSpaceOnUse"><circle cx="30" cy="30" r="4" fill="white" fillOpacity="0.1"/></pattern></defs><rect width="100%" height="100%" fill="url(#upgrade-dots)"/></svg></div>
            <div className="relative z-10">
              <div className="w-20 h-20 bg-white/20 rounded-full flex items-center justify-center mx-auto mb-6 shadow-lg backdrop-blur-sm"><Rocket size={40} className="text-white animate-bounce" /></div>
              <h2 className="text-4xl font-bold text-white mb-4">{t.cta.title}</h2>
              <p className="text-white/90 text-lg mb-8 max-w-2xl mx-auto leading-relaxed">{t.cta.description}</p>
              <button onClick={handleUpgrade} className="inline-flex items-center gap-3 px-8 py-4 bg-white text-amber-700 font-bold rounded-2xl hover:bg-gray-50 hover:scale-105 active:scale-95 transition-all duration-300 shadow-lg hover:shadow-xl group">
                <Crown size={24} className="group-hover:animate-pulse" />
                {t.cta.buttonText.replace('{price}', billingCycle === 'monthly' ? t.pricingCards.pro.priceMonthly : t.pricingCards.pro.priceYearly)}
                <Rocket size={20} className="group-hover:translate-x-1 transition-transform duration-300" />
              </button>
              <p className="text-white/70 text-sm mt-4">{t.cta.guarantee}</p>
            </div>
          </div>
        </section>
      </div>
      <style jsx>{`
        @keyframes blob { 0% { transform: translate(0px, 0px) scale(1); } 33% { transform: translate(30px, -50px) scale(1.1); } 66% { transform: translate(-20px, 20px) scale(0.9); } 100% { transform: translate(0px, 0px) scale(1); } }
        @keyframes float { 0%, 100% { transform: translateY(0px); } 50% { transform: translateY(-10px); } }
        .animate-blob { animation: blob 7s infinite; }
        .animation-delay-2000 { animation-delay: 2s; }
        .animation-delay-4000 { animation-delay: 4s; }
        .animate-float { animation: float 3s ease-in-out infinite; }
      `}</style>
    </main>
  );
}