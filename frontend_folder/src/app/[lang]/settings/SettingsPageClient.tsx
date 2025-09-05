// src/app/[lang]/settings/SettingsPageClient.tsx
'use client';

import React, { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { 
  Sun, 
  Moon, 
  Monitor, 
  Languages, 
  Trash2, 
  Save, 
  AlertTriangle,
  Bell,
  Shield,
  Download,
  Palette,
  Zap,
  Info,
  Settings
} from 'lucide-react';
import { getUserSettings, updateUserSettings, clearChatHistory, exportUserData } from '../../../../services/api';
import toast from 'react-hot-toast';

// =======================
// المكونات الفرعية المحسنة
// =======================

const SettingsCard: React.FC<{ title: string; description: string; children: React.ReactNode; icon: React.ElementType; variant?: 'default' | 'warning' | 'premium' }> = ({ title, description, children, icon: Icon, variant = 'default' }) => {
  const variants = {
    default: 'bg-white/80 dark:bg-gray-800/60 border-gray-200/50 dark:border-gray-700/50',
    warning: 'bg-red-50/80 dark:bg-red-900/20 border-red-200/50 dark:border-red-800/50',
    premium: 'bg-gradient-to-br from-amber-50/80 to-green-50/80 dark:from-amber-900/20 dark:to-green-900/20 border-amber-200/50 dark:border-amber-800/50'
  };

  return (
    <div className={`${variants[variant]} rounded-2xl border backdrop-blur-sm transition-all duration-300 hover:shadow-lg hover:shadow-teal-500/10 group`}>
      <div className="p-6 border-b border-gray-200/30 dark:border-gray-700/30">
        <div className="flex items-center gap-4">
          {Icon && (
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-teal-500 to-teal-600 flex items-center justify-center text-white shadow-md group-hover:shadow-lg transition-all duration-300">
              <Icon size={24} />
            </div>
          )}
          <div>
            <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-1">{title}</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">{description}</p>
          </div>
        </div>
      </div>
      <div className="p-6 space-y-6">
        {children}
      </div>
    </div>
  );
};

const SettingsRow: React.FC<{ title: string; description: string; children: React.ReactNode; badge?: string; isNew?: boolean; newText?: string }> = ({ title, description, children, badge, isNew = false, newText }) => (
  <div className="flex items-center justify-between group hover:bg-gray-50/50 dark:hover:bg-gray-800/30 -mx-2 px-2 py-3 rounded-lg transition-colors">
    <div className="flex-1">
      <div className="flex items-center gap-3">
        <h4 className="font-semibold text-gray-900 dark:text-gray-100">{title}</h4>
        {isNew && (
          <span className="px-2 py-1 text-xs font-bold bg-gradient-to-r from-teal-500 to-teal-600 text-white rounded-full">
            {newText}
          </span>
        )}
        {badge && (
          <span className="px-2 py-1 text-xs font-medium bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg">
            {badge}
          </span>
        )}
      </div>
      <p className="text-sm text-gray-600 dark:text-gray-400 mt-1 leading-relaxed">{description}</p>
    </div>
    <div className="ml-4">
      {children}
    </div>
  </div>
);

const ToggleSwitch: React.FC<{ enabled: boolean; setEnabled: (enabled: boolean) => void; size?: 'sm' | 'md' | 'lg' }> = ({ enabled, setEnabled, size = 'md' }) => {
  const sizes = {
    sm: { container: 'h-5 w-9', thumb: 'h-3 w-3', translate: enabled ? 'translate-x-5' : 'translate-x-1' },
    md: { container: 'h-6 w-11', thumb: 'h-4 w-4', translate: enabled ? 'translate-x-6' : 'translate-x-1' },
    lg: { container: 'h-7 w-13', thumb: 'h-5 w-5', translate: enabled ? 'translate-x-7' : 'translate-x-1' }
  };

  return (
    <button 
      onClick={() => setEnabled(!enabled)} 
      className={`relative inline-flex ${sizes[size].container} items-center rounded-full transition-all duration-300 focus:outline-none focus:ring-4 focus:ring-teal-500/20 ${
        enabled 
          ? 'bg-gradient-to-r from-teal-500 to-teal-600 shadow-md' 
          : 'bg-gray-300 dark:bg-gray-600 hover:bg-gray-400 dark:hover:bg-gray-500'
      }`}
    >
      <span className={`inline-block ${sizes[size].thumb} transform rounded-full bg-white transition-transform duration-300 shadow-sm ${sizes[size].translate}`} />
    </button>
  );
};

const ConfirmationModal: React.FC<{ isOpen: boolean; onClose: () => void; onConfirm: () => void; title: string; message: string; type?: 'danger' | 'warning'; dictionary: any }> = ({ isOpen, onClose, onConfirm, title, message, type = 'danger', dictionary }) => {
  useEffect(() => {
    if (isOpen) document.body.style.overflow = 'hidden';
    else document.body.style.overflow = 'unset';
    return () => { document.body.style.overflow = 'unset'; };
  }, [isOpen]);

  if (!isOpen) return null;

  const t = dictionary.settingsPage.modals;
  const typeConfig = {
    danger: { icon: AlertTriangle, iconBg: 'bg-red-100 dark:bg-red-900/30', iconColor: 'text-red-600 dark:text-red-400', confirmBg: 'bg-red-600 hover:bg-red-700', confirmText: t.clearHistory.confirm },
    warning: { icon: AlertTriangle, iconBg: 'bg-amber-100 dark:bg-amber-900/30', iconColor: 'text-amber-600 dark:text-amber-400', confirmBg: 'bg-amber-600 hover:bg-amber-700', confirmText: t.exportData.confirm }
  };
  const config = typeConfig[type];
  const IconComponent = config.icon;

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-md z-50 flex items-center justify-center animate-in fade-in duration-200" dir="rtl">
      <div className="bg-white dark:bg-gray-800 rounded-3xl shadow-2xl p-8 w-full max-w-md mx-4 border border-gray-200 dark:border-gray-700 animate-in zoom-in-95 duration-300">
        <div className="flex items-start gap-6 mb-6">
          <div className={`w-12 h-12 ${config.iconBg} ${config.iconColor} rounded-2xl flex items-center justify-center flex-shrink-0`}><IconComponent size={24} /></div>
          <div><h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-3">{title}</h2><p className="text-gray-600 dark:text-gray-400 leading-relaxed">{message}</p></div>
        </div>
        <div className="flex justify-end gap-4">
          <button onClick={onClose} className="px-6 py-3 rounded-xl bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-800 dark:text-gray-200 font-semibold transition-all duration-200 hover:scale-105 focus:outline-none focus:ring-4 focus:ring-gray-500/20">{t.cancel}</button>
          <button onClick={onConfirm} className={`px-6 py-3 rounded-xl ${config.confirmBg} text-white font-bold transition-all duration-200 hover:scale-105 focus:outline-none focus:ring-4 focus:ring-red-500/20`}>{config.confirmText}</button>
        </div>
      </div>
    </div>
  );
};

const ThemeSelector: React.FC<{ theme: string; setTheme: (theme: string) => void; dictionary: any }> = ({ theme, setTheme, dictionary }) => {
  const t = dictionary.settingsPage.appearance.themes;
  const themes = [
    { id: 'light', icon: Sun, ...t.light },
    { id: 'dark', icon: Moon, ...t.dark },
    { id: 'system', icon: Monitor, ...t.system }
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
      {themes.map(({ id, icon: Icon, label, description }) => (
        <button key={id} onClick={() => setTheme(id)} className={`p-4 rounded-2xl border-2 transition-all duration-300 group hover:scale-105 ${theme === id ? 'border-teal-500 bg-teal-50 dark:bg-teal-900/20 shadow-lg shadow-teal-500/20' : 'border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 hover:border-teal-300 dark:hover:border-teal-600'}`}>
          <div className="flex flex-col items-center text-center space-y-3">
            <div className={`w-12 h-12 rounded-xl flex items-center justify-center transition-colors ${theme === id ? 'bg-teal-500 text-white' : 'bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300 group-hover:bg-teal-100 dark:group-hover:bg-teal-900/30'}`}><Icon size={24} /></div>
            <div><div className={`font-semibold ${theme === id ? 'text-teal-700 dark:text-teal-300' : 'text-gray-700 dark:text-gray-300'}`}>{label}</div><div className="text-xs text-gray-500 dark:text-gray-400 mt-1">{description}</div></div>
          </div>
        </button>
      ))}
    </div>
  );
};

// =======================
// المكون الرئيسي المحسن
// =======================
export default function SettingsPageClient({ dictionary }: { dictionary: any }) {
  const [settings, setSettings] = useState({
    theme: 'system',
    language: 'ar',
    email_notifications: true,
    sms_notifications: false,
  });
  const [initialSettings, setInitialSettings] = useState({});
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isClearHistoryModalOpen, setIsClearHistoryModalOpen] = useState(false);
  const [isExportModalOpen, setIsExportModalOpen] = useState(false);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  const params = useParams();
  const lang = params.lang as string;
  const t = dictionary.settingsPage;

  useEffect(() => {
    const fetchSettings = async () => {
      setIsLoading(true);
      try {
        const data = await getUserSettings();
        const initialData = {
          theme: data.theme || 'system',
          language: data.language || lang,
          email_notifications: data.email_notifications ?? true,
          sms_notifications: data.sms_notifications ?? false,
        };
        setSettings(initialData);
        setInitialSettings(initialData);
      } catch (error: any) {
        toast.error(error.message || "Failed to load settings.");
      } finally {
        setIsLoading(false);
      }
    };
    fetchSettings();
  }, [lang]);

  useEffect(() => {
    if (!isLoading) {
      setHasUnsavedChanges(JSON.stringify(settings) !== JSON.stringify(initialSettings));
    }
  }, [settings, initialSettings, isLoading]);

  const handleSave = async () => {
    setIsSaving(true);
    toast.loading(t.saveBar.saving);
    try {
      const data = await updateUserSettings(settings);
      setInitialSettings(settings);
      setHasUnsavedChanges(false);
      toast.dismiss();
      toast.success(data.message || t.saveBar.success);
    } catch (error: any) {
      toast.dismiss();
      toast.error(error.message);
    } finally {
      setIsSaving(false);
    }
  };

  const handleReset = () => {
    setSettings(initialSettings);
  };

  const handleClearHistory = async () => {
    setIsClearHistoryModalOpen(false);
    toast.loading('Deleting history...');
    try {
      const response = await clearChatHistory();
      toast.dismiss();
      toast.success(response.message || t.modals.clearHistory.success);
    } catch (error: any) {
      toast.dismiss();
      toast.error(error.message);
    }
  };

  const handleExportData = async () => {
    setIsExportModalOpen(false);
    toast.loading('Exporting data...');
    try {
      const response = await exportUserData();
      toast.dismiss();
      toast.success(response.message || t.modals.exportData.success);
    } catch (error: any) {
      toast.dismiss();
      toast.error(error.message);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 via-white to-gray-100 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
        <div className="w-16 h-16 border-4 border-dashed rounded-full animate-spin border-teal-500"></div>
      </div>
    );
  }

  return (
    <>
      <ConfirmationModal isOpen={isClearHistoryModalOpen} onClose={() => setIsClearHistoryModalOpen(false)} onConfirm={handleClearHistory} title={t.modals.clearHistory.title} message={t.modals.clearHistory.message} type="danger" dictionary={dictionary} />
      <ConfirmationModal isOpen={isExportModalOpen} onClose={() => setIsExportModalOpen(false)} onConfirm={handleExportData} title={t.modals.exportData.title} message={t.modals.exportData.message} type="warning" dictionary={dictionary} />

      <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-100 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 font-arabic transition-all duration-500">
        <div className="sticky top-0 z-40 bg-white/80 dark:bg-gray-900/80 backdrop-blur-xl border-b border-gray-200/50 dark:border-gray-700/50">
          <div className="max-w-4xl mx-auto px-6 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-teal-500 to-teal-600 flex items-center justify-center text-white"><Settings size={20} /></div>
                <div><h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">{t.header.title}</h1><p className="text-sm text-gray-600 dark:text-gray-400">{t.header.description}</p></div>
              </div>
              {hasUnsavedChanges && <div className="flex items-center gap-3"><span className="text-sm text-amber-600 dark:text-amber-400 font-medium">{t.header.unsavedChanges}</span><div className="w-2 h-2 bg-amber-500 rounded-full animate-pulse"></div></div>}
            </div>
          </div>
        </div>

        <div className="max-w-4xl mx-auto px-6 py-8">
          <div className="space-y-8">
            <SettingsCard title={t.appearance.title} description={t.appearance.description} icon={Palette}>
              <div><h5 className="font-semibold text-gray-900 dark:text-gray-100 mb-4">{t.appearance.theme}</h5><ThemeSelector theme={settings.theme} setTheme={(value) => setSettings({...settings, theme: value})} dictionary={dictionary} /></div>
              <SettingsRow title={t.appearance.preview.title} description={t.appearance.preview.description} isNew={true} newText={t.appearance.preview.new}><ToggleSwitch enabled={false} setEnabled={() => {}} /></SettingsRow>
            </SettingsCard>

            <SettingsCard title={t.language.title} description={t.language.description} icon={Languages}>
              <SettingsRow title={t.language.interfaceLanguage.title} description={t.language.interfaceLanguage.description} badge={t.language.interfaceLanguage.badge}>
                <select value={settings.language} onChange={e => setSettings({...settings, language: e.target.value})} className="bg-gray-100 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-xl px-4 py-2 text-sm font-medium focus:ring-4 focus:ring-teal-500/20 focus:border-teal-500 transition-all">
                  {Object.keys(t.language.languages).map(langKey => <option key={langKey} value={langKey}>{t.language.languages[langKey]}</option>)}
                </select>
              </SettingsRow>
            </SettingsCard>

            <SettingsCard title={t.notifications.title} description={t.notifications.description} icon={Bell}>
              <SettingsRow title={t.notifications.enableNotifications.title} description={t.notifications.enableNotifications.description}><ToggleSwitch enabled={settings.email_notifications} setEnabled={(value) => setSettings({...settings, email_notifications: value})} /></SettingsRow>
              {/* Dummy setting for sounds, you can connect it to a real state if needed */}
              <SettingsRow title={t.notifications.sounds.title} description={t.notifications.sounds.description}><ToggleSwitch enabled={true} setEnabled={() => {}} /></SettingsRow>
            </SettingsCard>

            <SettingsCard title={t.dataManagement.title} description={t.dataManagement.description} icon={Shield}>
              {/* Dummy setting for auto-save, you can connect it to a real state if needed */}
              <SettingsRow title={t.dataManagement.autoSave.title} description={t.dataManagement.autoSave.description}><ToggleSwitch enabled={true} setEnabled={() => {}} /></SettingsRow>
              <div className="border-t border-gray-200 dark:border-gray-700 pt-6">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <button onClick={() => setIsExportModalOpen(true)} className="flex items-center justify-center gap-3 p-4 rounded-xl border-2 border-teal-200 dark:border-teal-700 bg-teal-50 dark:bg-teal-900/20 text-teal-700 dark:text-teal-300 hover:bg-teal-100 dark:hover:bg-teal-900/40 transition-all duration-200 hover:scale-105 group"><Download size={20} className="group-hover:scale-110 transition-transform" /><span className="font-semibold">{t.dataManagement.exportData}</span></button>
                  <button onClick={() => setIsClearHistoryModalOpen(true)} className="flex items-center justify-center gap-3 p-4 rounded-xl border-2 border-red-200 dark:border-red-700 bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 hover:bg-red-100 dark:hover:bg-red-900/40 transition-all duration-200 hover:scale-105 group"><Trash2 size={20} className="group-hover:scale-110 transition-transform" /><span className="font-semibold">{t.dataManagement.clearHistory}</span></button>
                </div>
              </div>
            </SettingsCard>

            <SettingsCard title={t.advanced.title} description={t.advanced.description} icon={Zap}>
              <SettingsRow title={t.advanced.developerMode.title} description={t.advanced.developerMode.description} badge={t.advanced.developerMode.badge}><ToggleSwitch enabled={false} setEnabled={() => {}} /></SettingsRow>
              <SettingsRow title={t.advanced.analytics.title} description={t.advanced.analytics.description}><ToggleSwitch enabled={true} setEnabled={() => {}} /></SettingsRow>
            </SettingsCard>
          </div>

          <div className="sticky bottom-6 mt-12">
            <div className="bg-white/90 dark:bg-gray-800/90 backdrop-blur-xl rounded-2xl border border-gray-200/50 dark:border-gray-700/50 shadow-xl p-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-green-500 to-green-600 flex items-center justify-center text-white"><Info size={20} /></div>
                  <div><p className="font-semibold text-gray-900 dark:text-gray-100">{t.saveBar.title}</p><p className="text-sm text-gray-600 dark:text-gray-400">{t.saveBar.description}</p></div>
                </div>
                <div className="flex items-center gap-4">
                  <button onClick={handleReset} className="px-6 py-3 rounded-xl text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-all duration-200 font-medium">{t.saveBar.reset}</button>
                  <button onClick={handleSave} disabled={isSaving || !hasUnsavedChanges} className="px-8 py-3 rounded-xl bg-gradient-to-r from-teal-500 to-teal-600 text-white font-bold hover:from-teal-600 hover:to-teal-700 transition-all duration-200 hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none flex items-center gap-3 shadow-lg shadow-teal-500/30">
                    {isSaving ? (<><div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>{t.saveBar.saving}</>) : (<><Save size={20} />{t.saveBar.save}</>)}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}