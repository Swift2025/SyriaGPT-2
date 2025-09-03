// src/app/api/chat/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { GoogleGenerativeAI } from '@google/generative-ai';
import { getAdvancedFallback } from './fallback';

// --- إعداد وتهيئة Gemini ---
const GEMINI_API_KEY = process.env.GEMINI_API_KEY || process.env.NEXT_PUBLIC_GEMINI_API_KEY;

console.log('🔑 حالة مفتاح API:', GEMINI_API_KEY ? 'موجود' : 'مفقود');

let genAI: GoogleGenerativeAI | null = null;
let model: any = null;
let isGeminiAvailable = false;

// تهيئة Gemini في المستوى العلوي
try {
  if (GEMINI_API_KEY) {
    genAI = new GoogleGenerativeAI(GEMINI_API_KEY);
    model = genAI.getGenerativeModel({
      model: "gemini-1.5-flash",
      generationConfig: {
        temperature: 0.9,
        topK: 64,
        topP: 0.95,
        maxOutputTokens: 8192,
      },
    });
    isGeminiAvailable = true;
    console.log('✅ Gemini تم تهيئته بنجاح');
  } else {
    console.error('❌ مفتاح Gemini API غير موجود');
    isGeminiAvailable = false;
  }
} catch (error: any) {
  console.error('❌ خطأ في تهيئة Gemini:', error.message);
  isGeminiAvailable = false;
  model = null;
}

// --- Prompt محسن للسياق السوري ---
const SYSTEM_PROMPT = `أنت SyriaGPT، خبير متخصص في سوريا بجميع جوانبها. أنت تملك معرفة عميقة ومفصلة عن التاريخ، الجغرافيا، المطبخ، والثقافة السورية. أسلوبك ودود، مفصل، وعملي. لا تقل أبداً "لا أعرف"، بل قدم أفضل معلومات متاحة.`;

// --- معالج الطلبات الرئيسي ---
export async function POST(request: NextRequest) {
  try {
    const { message, conversationHistory = [] } = await request.json();

    if (!message || typeof message !== 'string' || message.trim() === '') {
      return NextResponse.json({ error: 'يرجى إدخال رسالة صحيحة.' }, { status: 400 });
    }

    const userMessage = message.trim();
    let responseText = '';
    let source = 'unknown';

    // محاولة استخدام Gemini أولاً
    if (isGeminiAvailable && model) {
      try {
        let fullContext = SYSTEM_PROMPT + '\n\n--- تاريخ المحادثة ---\n';
        conversationHistory.slice(-8).forEach((msg: any) => {
            fullContext += `${msg.sender === 'user' ? 'المستخدم' : 'SyriaGPT'}: ${msg.content}\n`;
        });
        fullContext += `--- نهاية التاريخ ---\n\nالمستخدم الحالي: ${userMessage}\nSyriaGPT: `;
        
        console.log('📤 إرسال طلب إلى Gemini...');
        
        const result = await model.generateContent(fullContext);
        const response = await result.response;
        responseText = response.text();

        if (!responseText || !responseText.trim()) {
          throw new Error('رد فارغ من Gemini');
        }
        
        source = 'gemini';
        console.log('✅ تم الحصول على رد من Gemini بنجاح');

      } catch (geminiError: any) {
        console.error('❌ خطأ في Gemini:', geminiError.message);
        
        // في حالة الخطأ 403، نوضح المشكلة
        if (geminiError.message.includes('403')) {
          console.error('⚠️ خطأ 403: مفتاح API غير صالح أو لا يملك الصلاحيات المطلوبة');
          console.error('💡 الحل: احصل على مفتاح API جديد من https://aistudio.google.com/apikey');
        }

        responseText = await getAdvancedFallback(userMessage, conversationHistory);
        source = 'advanced_fallback';
        console.log('⚠️ تم استخدام النظام الاحتياطي بسبب خطأ Gemini');
      }
    } else {
      responseText = await getAdvancedFallback(userMessage, conversationHistory);
      source = 'advanced_fallback';
      console.log('ℹ️ Gemini غير متاح، تم استخدام النظام الاحتياطي');
    }

    // التأكد من وجود رد نهائي
    if (!responseText || !responseText.trim()) {
      responseText = `أعتذر، واجهت صعوبة في معالجة طلبك. هل يمكنك إعادة صياغة السؤال؟`;
      source = 'final_fallback';
    }

    return NextResponse.json({
      message: responseText.trim(),
      timestamp: new Date().toISOString(),
      source,
      gemini_status: isGeminiAvailable ? 'متاح' : 'غير متاح'
    });

  } catch (error: any) {
    console.error('💥 خطأ عام في معالج الطلب:', error);
    return NextResponse.json({
      message: 'أعتذر، حدث خطأ غير متوقع. فريقنا يعمل على إصلاحه. الرجاء المحاولة مرة أخرى بعد قليل.',
      timestamp: new Date().toISOString(),
      source: 'emergency_error',
      error_details: process.env.NODE_ENV === 'development' ? error.message : undefined
    }, { status: 500 });
  }
}

// --- معالج GET لاختبار حالة الـ API ---
export async function GET() {
  return NextResponse.json({
    message: 'SyriaGPT API - v3.3 (Simplified)',
    status: 'active',
    gemini_available: isGeminiAvailable,
    api_key_status: GEMINI_API_KEY ? 'موجود' : 'مفقود',
    timestamp: new Date().toISOString(),
  });
}