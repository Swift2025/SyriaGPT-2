// src/app/api/files/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { GoogleGenerativeAI } from '@google/generative-ai';

// تهيئة Gemini AI للملفات
const GEMINI_API_KEY = process.env.GEMINI_API_KEY || process.env.NEXT_PUBLIC_GEMINI_API_KEY;

let genAI: GoogleGenerativeAI | null = null;
let model: any = null;

try {
  if (GEMINI_API_KEY) {
    genAI = new GoogleGenerativeAI(GEMINI_API_KEY);
    // استخدام نفس النموذج المستخدم في الشات
    model = genAI.getGenerativeModel({ 
      model: "gemini-1.5-flash",
      generationConfig: {
        temperature: 0.7,
        topK: 40,
        topP: 0.95,
        maxOutputTokens: 8192,
      }
    });
    console.log('✅ Gemini للملفات تم تهيئته بنجاح');
  } else {
    console.error('❌ مفتاح Gemini API غير موجود في معالج الملفات');
  }
} catch (error: any) {
  console.error('❌ خطأ في تهيئة Gemini للملفات:', error.message);
}

// دالة لاستخراج النص من ملف PDF
async function extractTextFromPDF(file: File): Promise<string> {
  try {
    // للمرحلة الحالية، نعيد محتوى أساسي
    // يمكن لاحقاً تطبيق مكتبة pdf-parse أو pdf2pic
    const arrayBuffer = await file.arrayBuffer();
    const text = `تم رفع ملف PDF: ${file.name}
    
حجم الملف: ${(file.size / 1024).toFixed(2)} كيلو بايت
تاريخ الرفع: ${new Date().toLocaleDateString('ar-EG')}

ملاحظة: استخراج النص من PDF يتطلب مكتبة متخصصة.
يمكنك نسخ النص ولصقه مباشرة في الرسالة للحصول على تحليل أفضل.`;
    
    return text;
  } catch (error: any) {
    console.error('خطأ في استخراج النص من PDF:', error);
    return `فشل في قراءة ملف PDF: ${file.name}`;
  }
}

// دالة لاستخراج النص من ملف Word
async function extractTextFromWord(file: File): Promise<string> {
  try {
    // للمرحلة الحالية، نعيد محتوى أساسي
    // يمكن لاحقاً تطبيق مكتبة mammoth
    const arrayBuffer = await file.arrayBuffer();
    const text = `تم رفع ملف Word: ${file.name}
    
حجم الملف: ${(file.size / 1024).toFixed(2)} كيلو بايت
تاريخ الرفع: ${new Date().toLocaleDateString('ar-EG')}

ملاحظة: استخراج النص من Word يتطلب مكتبة متخصصة.
يمكنك نسخ النص ولصقه مباشرة في الرسالة للحصول على تحليل أفضل.`;
    
    return text;
  } catch (error: any) {
    console.error('خطأ في استخراج النص من Word:', error);
    return `فشل في قراءة ملف Word: ${file.name}`;
  }
}

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData();
    const file = formData.get('file') as File;
    const message = formData.get('message') as string;

    if (!file) {
      return NextResponse.json(
        { error: 'لم يتم رفع ملف' },
        { status: 400 }
      );
    }

    // التحقق من نوع الملف
    const allowedTypes = [
      'application/pdf',
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'text/plain',
      'text/csv'
    ];

    if (!allowedTypes.includes(file.type)) {
      return NextResponse.json(
        { error: `نوع الملف غير مدعوم: ${file.type}` },
        { status: 400 }
      );
    }

    // التحقق من حجم الملف (10 ميجابايت)
    if (file.size > 10 * 1024 * 1024) {
      return NextResponse.json(
        { error: 'حجم الملف كبير جداً. الحد الأقصى 10 ميجابايت' },
        { status: 400 }
      );
    }

    let extractedText = '';

    // استخراج النص حسب نوع الملف
    try {
      if (file.type === 'application/pdf') {
        extractedText = await extractTextFromPDF(file);
      } else if (file.type.includes('word') || file.type.includes('document')) {
        extractedText = await extractTextFromWord(file);
      } else if (file.type === 'text/plain' || file.type === 'text/csv') {
        extractedText = await file.text();
      } else {
        extractedText = `تم رفع الملف: ${file.name} بنجاح، لكن لا يمكن استخراج النص منه مباشرة.`;
      }
    } catch (extractError: any) {
      console.error('خطأ في استخراج النص:', extractError);
      extractedText = `تم رفع الملف: ${file.name} لكن حدث خطأ في استخراج المحتوى.`;
    }

    // محاولة التحليل بواسطة Gemini
    let analysisText = '';
    let analysisSource = 'fallback';

    if (model && GEMINI_API_KEY) {
      try {
        // إنشاء prompt للتحليل
        const analysisPrompt = `قم بتحليل وتلخيص المحتوى التالي باللغة العربية:

اسم الملف: ${file.name}
نوع الملف: ${file.type}
حجم الملف: ${(file.size / 1024).toFixed(2)} كيلو بايت

المحتوى:
${extractedText}

${message ? `\nالسؤال المطروح: ${message}` : ''}

يرجى تقديم:
1. ملخص للمحتوى
2. النقاط الرئيسية
3. ${message ? 'إجابة مفصلة على السؤال المطروح' : 'استنتاجات وملاحظات مهمة'}

الرد باللغة العربية بأسلوب واضح ومفيد:`;

        const result = await model.generateContent(analysisPrompt);
        const response = await result.response;
        analysisText = response.text();
        analysisSource = 'gemini';
        
        console.log('✅ تم تحليل الملف بواسطة Gemini');

      } catch (geminiError: any) {
        console.error('❌ خطأ في تحليل Gemini للملف:', geminiError.message);
        
        // رد احتياطي
        analysisText = `تم رفع الملف "${file.name}" بنجاح!

📄 تفاصيل الملف:
- النوع: ${file.type}
- الحجم: ${(file.size / 1024).toFixed(2)} كيلو بايت
- تاريخ الرفع: ${new Date().toLocaleDateString('ar-EG')}

${message ? `\n💭 سؤالك: ${message}\n\n` : ''}

للحصول على تحليل أفضل للملف، يمكنك:
1. نسخ النص من الملف ولصقه مباشرة في المحادثة
2. طرح أسئلة محددة حول محتوى الملف
3. تجربة ملف أصغر حجماً إذا كان كبيراً

كيف يمكنني مساعدتك أكثر مع هذا الملف؟`;
        
        analysisSource = 'fallback';
      }
    } else {
      // رد احتياطي عندما لا يكون Gemini متاحاً
      analysisText = `تم استلام الملف "${file.name}" بنجاح!

📊 معلومات الملف:
- النوع: ${file.type}
- الحجم: ${(file.size / 1024).toFixed(2)} كيلو بايت

${message ? `سؤالك: ${message}\n\n` : ''}

عذراً، خدمة التحليل التلقائي غير متاحة حالياً. يمكنك:
- نسخ النص من الملف ولصقه للحصول على إجابات
- طرح أسئلة محددة حول المحتوى
- المحاولة مرة أخرى بعد قليل`;

      analysisSource = 'no_gemini';
    }

    return NextResponse.json({
      success: true,
      fileName: file.name,
      fileSize: file.size,
      fileType: file.type,
      extractedText: extractedText.length > 500 ? extractedText.substring(0, 500) + '...' : extractedText,
      analysis: analysisText.trim(),
      analysisSource,
      timestamp: new Date().toISOString()
    });

  } catch (error: any) {
    console.error('💥 خطأ عام في معالجة الملف:', error);
    
    return NextResponse.json(
      { 
        error: 'حدث خطأ في معالجة الملف. يرجى المحاولة مرة أخرى.',
        details: process.env.NODE_ENV === 'development' ? error.message : undefined
      },
      { status: 500 }
    );
  }
}
  