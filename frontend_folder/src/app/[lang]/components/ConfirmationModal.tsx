// src/app/components/ConfirmationModal.tsx
'use client';

import React from 'react';
import { AlertTriangle } from 'lucide-react';

interface ConfirmationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  icon?: React.ReactNode;
}

const ConfirmationModal: React.FC<ConfirmationModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmText = 'نعم، أنا متأكد',
  cancelText = 'إلغاء',
  icon = <AlertTriangle size={24} />,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center" dir="rtl">
      <div className="bg-[#3d3a3b] dark:bg-brand-text-dark text-brand-cream rounded-2xl shadow-lg p-6 w-full max-w-md m-4 border border-white/10 animate-[fadeIn_0.2s_ease-in-out]">
        <div className="flex items-start gap-4">
          <div className="w-10 h-10 bg-red-500/20 text-red-500 rounded-full flex items-center justify-center flex-shrink-0">
            {icon}
          </div>
          <div>
            <h2 className="text-xl font-bold mb-2">{title}</h2>
            <p className="text-sm text-gray-300">{message}</p>
          </div>
        </div>
        <div className="flex justify-end gap-4 mt-6">
          <button onClick={onClose} className="px-6 py-2 rounded-lg bg-gray-500/50 hover:bg-gray-500/70 text-white font-medium transition-colors">
            {cancelText}
          </button>
          <button onClick={onConfirm} className="px-6 py-2 rounded-lg bg-red-600 hover:bg-red-700 text-white font-bold transition-colors">
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ConfirmationModal;