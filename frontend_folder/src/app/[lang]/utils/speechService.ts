'use client';

// تعريفات TypeScript محسنة لواجهة التعرف على الكلام
interface SpeechRecognitionResult {
  readonly isFinal: boolean;
  readonly [key: number]: {
    readonly transcript: string;
    readonly confidence: number;
  };
  readonly length: number;
}

interface SpeechRecognitionResultList {
  readonly [key: number]: SpeechRecognitionResult;
  readonly length: number;
}

interface SpeechRecognitionEvent {
  readonly results: SpeechRecognitionResultList;
  readonly resultIndex: number;
}

interface SpeechRecognitionErrorEvent {
  readonly error: string;
  readonly message?: string;
}

interface SpeechRecognition extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  maxAlternatives: number;
  onstart: ((this: SpeechRecognition, ev: Event) => any) | null;
  onresult: ((this: SpeechRecognition, ev: SpeechRecognitionEvent) => any) | null;
  onerror: ((this: SpeechRecognition, ev: SpeechRecognitionErrorEvent) => any) | null;
  onend: ((this: SpeechRecognition, ev: Event) => any) | null;
  onnomatch: ((this: SpeechRecognition, ev: SpeechRecognitionEvent) => any) | null;
  onspeechstart: ((this: SpeechRecognition, ev: Event) => any) | null;
  onspeechend: ((this: SpeechRecognition, ev: Event) => any) | null;
  onaudiostart: ((this: SpeechRecognition, ev: Event) => any) | null;
  onaudioend: ((this: SpeechRecognition, ev: Event) => any) | null;
  onsoundstart: ((this: SpeechRecognition, ev: Event) => any) | null;
  onsoundend: ((this: SpeechRecognition, ev: Event) => any) | null;
  start(): void;
  stop(): void;
  abort(): void;
}

declare global {
  interface Window {
    SpeechRecognition: {
      new (): SpeechRecognition;
    };
    webkitSpeechRecognition: {
      new (): SpeechRecognition;
    };
  }
}

// خيارات خدمة التحويل الصوتي
interface SpeechServiceOptions {
  language?: string;
  continuous?: boolean;
  interimResults?: boolean;
  maxAlternatives?: number;
  onResult: (text: string, isFinal?: boolean) => void;
  onError: (error: string) => void;
  onStart: () => void;
  onEnd: () => void;
  onSpeechStart?: () => void;
  onSpeechEnd?: () => void;
}

class EnhancedSpeechService {
  private recognition: SpeechRecognition | null = null;
  private isListening = false;
  private isInitialized = false;
  private currentOptions: SpeechServiceOptions | null = null;
  private retryCount = 0;
  private maxRetries = 3;
  private restartTimeout: NodeJS.Timeout | null = null;

  constructor() {
    this.initialize();
  }

  private initialize(): void {
    if (typeof window === 'undefined') return;

    try {
      const SpeechRecognitionAPI = window.SpeechRecognition || window.webkitSpeechRecognition;
      
      if (SpeechRecognitionAPI) {
        this.recognition = new SpeechRecognitionAPI();
        this.isInitialized = true;
        console.log('تم تهيئة خدمة التحويل الصوتي بنجاح');
      } else {
        console.warn('API التحويل الصوتي غير مدعوم');
      }
    } catch (error) {
      console.error('فشل في تهيئة خدمة التحويل الصوتي:', error);
    }
  }

  isSupported(): boolean {
    return this.isInitialized && !!this.recognition;
  }

  isCurrentlyListening(): boolean {
    return this.isListening;
  }

  private setupRecognition(options: SpeechServiceOptions): void {
    if (!this.recognition) return;

    // إعداد خصائص التعرف
    this.recognition.lang = options.language || 'ar-SA';
    this.recognition.continuous = options.continuous ?? false;
    this.recognition.interimResults = options.interimResults ?? true;
    this.recognition.maxAlternatives = options.maxAlternatives ?? 1;

    // معالج بداية التسجيل
    this.recognition.onstart = () => {
      console.log('بدأ التعرف الصوتي');
      this.isListening = true;
      this.retryCount = 0;
      options.onStart();
    };

    // معالج النتائج
    this.recognition.onresult = (event) => {
      try {
        let finalTranscript = '';
        let interimTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; i++) {
          const result = event.results[i];
          const transcript = result[0].transcript;

          if (result.isFinal) {
            finalTranscript += transcript;
          } else {
            interimTranscript += transcript;
          }
        }

        if (finalTranscript) {
          console.log('نتيجة نهائية:', finalTranscript);
          options.onResult(finalTranscript.trim(), true);
        } else if (interimTranscript && options.interimResults) {
          console.log('نتيجة مؤقتة:', interimTranscript);
          options.onResult(interimTranscript.trim(), false);
        }
      } catch (error) {
        console.error('خطأ في معالجة النتائج:', error);
        options.onError('خطأ في معالجة النتائج الصوتية');
      }
    };

    // معالج الأخطاء المحسن
    this.recognition.onerror = (event) => {
      console.error('خطأ في التعرف الصوتي:', event.error);
      
      const errorMessages: { [key: string]: string } = {
        'no-speech': 'لم يتم اكتشاف أي كلام. تأكد من التحدث بوضوح.',
        'audio-capture': 'لا يمكن الوصول للميكروفون. تأكد من توصيله بشكل صحيح.',
        'not-allowed': 'تم رفض الإذن. يرجى السماح للموقع باستخدام الميكروفون.',
        'network': 'خطأ في الشبكة. تحقق من اتصالك بالإنترنت.',
        'service-not-allowed': 'خدمة التعرف الصوتي غير متاحة.',
        'bad-grammar': 'خطأ في قواعد التعرف الصوتي.',
        'language-not-supported': 'اللغة المحددة غير مدعومة.'
      };

      const userFriendlyError = errorMessages[event.error] || `خطأ غير معروف: ${event.error}`;
      
      // محاولة إعادة التشغيل للأخطاء القابلة للاستعادة
      if (['no-speech', 'audio-capture', 'network'].includes(event.error) && this.retryCount < this.maxRetries) {
        this.retryCount++;
        console.log(`محاولة إعادة التشغيل ${this.retryCount}/${this.maxRetries}`);
        
        this.restartTimeout = setTimeout(() => {
          if (this.currentOptions) {
            this.startListening(this.currentOptions);
          }
        }, 1000);
      } else {
        this.isListening = false;
        options.onError(userFriendlyError);
      }
    };

    // معالج انتهاء التسجيل
    this.recognition.onend = () => {
      console.log('انتهى التعرف الصوتي');
      this.isListening = false;
      options.onEnd();
    };

    // معالجات إضافية للحصول على تجربة أفضل
    this.recognition.onspeechstart = () => {
      console.log('بدأ الكلام');
      options.onSpeechStart?.();
    };

    this.recognition.onspeechend = () => {
      console.log('انتهى الكلام');
      options.onSpeechEnd?.();
    };

    this.recognition.onaudiostart = () => {
      console.log('بدأ التقاط الصوت');
    };

    this.recognition.onaudioend = () => {
      console.log('انتهى التقاط الصوت');
    };
  }

  startListening(options: SpeechServiceOptions): boolean {
    if (!this.isSupported()) {
      options.onError('التحويل الصوتي غير مدعوم في هذا المتصفح. استخدم Chrome أو Edge.');
      return false;
    }

    if (this.isListening) {
      console.warn('التعرف الصوتي يعمل بالفعل');
      return false;
    }

    try {
      this.currentOptions = options;
      this.setupRecognition(options);
      
      if (this.recognition) {
        this.recognition.start();
        return true;
      }
    } catch (error) {
      console.error('فشل في بدء التعرف الصوتي:', error);
      options.onError('فشل في بدء التعرف الصوتي');
      this.isListening = false;
    }

    return false;
  }

  stopListening(): void {
    if (this.restartTimeout) {
      clearTimeout(this.restartTimeout);
      this.restartTimeout = null;
    }

    if (this.recognition && this.isListening) {
      try {
        this.recognition.stop();
        console.log('تم إيقاف التعرف الصوتي');
      } catch (error) {
        console.error('خطأ في إيقاف التعرف الصوتي:', error);
      }
    }
    
    this.isListening = false;
    this.currentOptions = null;
    this.retryCount = 0;
  }

  abortListening(): void {
    if (this.restartTimeout) {
      clearTimeout(this.restartTimeout);
      this.restartTimeout = null;
    }

    if (this.recognition && this.isListening) {
      try {
        this.recognition.abort();
        console.log('تم إلغاء التعرف الصوتي');
      } catch (error) {
        console.error('خطأ في إلغاء التعرف الصوتي:', error);
      }
    }
    
    this.isListening = false;
    this.currentOptions = null;
    this.retryCount = 0;
  }

  // فحص الدعم للغة معينة
  static getSupportedLanguages(): string[] {
    return [
      'ar-SA', // العربية السعودية
      'ar-EG', // العربية المصرية
      'ar-AE', // العربية الإماراتية
      'ar-JO', // العربية الأردنية
      'ar-LB', // العربية اللبنانية
      'en-US', // الإنجليزية الأمريكية
      'en-GB', // الإنجليزية البريطانية
    ];
  }

  // اختبار الميكروفون
  static async testMicrophone(): Promise<boolean> {
    if (typeof window === 'undefined' || !navigator.mediaDevices?.getUserMedia) {
      return false;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        } 
      });
      
      // اختبار مستوى الصوت
      const audioContext = new AudioContext();
      const source = audioContext.createMediaStreamSource(stream);
      const analyser = audioContext.createAnalyser();
      source.connect(analyser);

      // تنظيف الموارد
      stream.getTracks().forEach(track => track.stop());
      await audioContext.close();
      
      return true;
    } catch (error) {
      console.error('فشل اختبار الميكروفون:', error);
      return false;
    }
  }
}

// طلب إذن الميكروفون مع تحسينات
export async function requestMicrophonePermission(): Promise<boolean> {
  if (typeof window === 'undefined') return false;

  try {
    // فحص الإذن الحالي
    const permission = await navigator.permissions?.query({ name: 'microphone' as PermissionName });
    
    if (permission?.state === 'granted') {
      return true;
    } else if (permission?.state === 'denied') {
      return false;
    }

    // طلب الإذن عبر getUserMedia
    return await EnhancedSpeechService.testMicrophone();
  } catch (error) {
    console.error('خطأ في طلب إذن الميكروفون:', error);
    return false;
  }
}

// تصدير الخدمة
export const speechService = new EnhancedSpeechService();
export default EnhancedSpeechService;