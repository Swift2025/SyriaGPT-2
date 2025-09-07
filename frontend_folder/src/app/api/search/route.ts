// src/app/api/search/route.ts
import { NextRequest, NextResponse } from 'next/server';

interface QAPair {
  id: string;
  question_variants: string[];
  answer: string;
  keywords: string[];
  confidence: number;
  source: string;
}

interface KnowledgeData {
  category: string;
  description: string;
  qa_pairs: QAPair[];
}

// كاش بسيط في الذاكرة
const searchCache = new Map<string, { answer: string; timestamp: number }>();
const CACHE_DURATION = 5 * 60 * 1000; // 5 دقائق

// تحميل البيانات المحلية
let localData: KnowledgeData[] = [];
let dataLoaded = false;

/**
 * تحميل البيانات المحلية من مجلد data
 */
async function loadLocalData(): Promise<void> {
  if (dataLoaded) return;

  try {
    const files = [
      'general.json',
      'cities.json', 
      'culture.json',
      'economy.json',
      'government.json',
      'Real_post_liberation_events.json'
    ];

    const loadPromises = files.map(async (file) => {
      try {
        const response = await fetch(`http://localhost:3000/data/syria_knowledge/${file}`);
        if (response.ok) {
          const data: KnowledgeData = await response.json();
          return data;
        }
      } catch (error) {
        console.warn(`Failed to load ${file}:`, error);
      }
      return null;
    });

    const results = await Promise.all(loadPromises);
    localData = results.filter((data): data is KnowledgeData => data !== null);
    dataLoaded = true;
    
    console.log(`✅ تم تحميل ${localData.length} ملف بيانات محلية`);
  } catch (error) {
    console.error('❌ فشل في تحميل البيانات المحلية:', error);
  }
}

/**
 * البحث في الكاش
 */
function searchInCache(question: string): string | null {
  const normalizedQuestion = question.toLowerCase().trim();
  
  for (const [cachedQuestion, cachedData] of searchCache.entries()) {
    if (Date.now() - cachedData.timestamp > CACHE_DURATION) {
      searchCache.delete(cachedQuestion);
      continue;
    }
    
    if (cachedQuestion.includes(normalizedQuestion) || normalizedQuestion.includes(cachedQuestion)) {
      console.log('🎯 تم العثور على إجابة في الكاش');
      return cachedData.answer;
    }
  }
  
  return null;
}

/**
 * البحث في البيانات المحلية
 */
function searchInLocalData(question: string): string | null {
  const normalizedQuestion = question.toLowerCase().trim();
  
  // إعطاء أولوية للملفات المهمة
  const priorityCategories = ['government', 'general', 'modern_syria'];
  const sortedData = [...localData].sort((a, b) => {
    const aIndex = priorityCategories.indexOf(a.category);
    const bIndex = priorityCategories.indexOf(b.category);
    if (aIndex === -1 && bIndex === -1) return 0;
    if (aIndex === -1) return 1;
    if (bIndex === -1) return -1;
    return aIndex - bIndex;
  });
  
  for (const category of sortedData) {
    for (const qaPair of category.qa_pairs) {
      // البحث في الأسئلة
      for (const variant of qaPair.question_variants) {
        if (variant.toLowerCase().includes(normalizedQuestion) || 
            normalizedQuestion.includes(variant.toLowerCase())) {
          console.log(`📚 تم العثور على إجابة في البيانات المحلية (${category.category})`);
          return qaPair.answer;
        }
      }
      
      // البحث في الكلمات المفتاحية
      for (const keyword of qaPair.keywords) {
        if (normalizedQuestion.includes(keyword.toLowerCase())) {
          console.log(`🔍 تم العثور على إجابة بالكلمات المفتاحية (${category.category})`);
          return qaPair.answer;
        }
      }
      
      // البحث في الإجابة أيضاً
      if (qaPair.answer.toLowerCase().includes(normalizedQuestion)) {
        console.log(`📖 تم العثور على إجابة في محتوى الإجابة (${category.category})`);
        return qaPair.answer;
      }
    }
  }
  
  return null;
}

/**
 * البحث المتقدم في البيانات المحلية (بحث دلالي بسيط)
 */
function advancedSearchInLocalData(question: string): string | null {
  const normalizedQuestion = question.toLowerCase().trim();
  const questionWords = normalizedQuestion.split(/\s+/);
  
  let bestMatch: { qaPair: QAPair; score: number; category: string } | null = null;
  
  for (const category of localData) {
    for (const qaPair of category.qa_pairs) {
      let score = 0;
      
      // البحث في الأسئلة
      for (const variant of qaPair.question_variants) {
        const variantWords = variant.toLowerCase().split(/\s+/);
        const commonWords = questionWords.filter(word => 
          variantWords.some(variantWord => 
            variantWord.includes(word) || word.includes(variantWord)
          )
        );
        score += commonWords.length * 2; // وزن أعلى للأسئلة
      }
      
      // البحث في الكلمات المفتاحية
      for (const keyword of qaPair.keywords) {
        if (questionWords.some(word => 
          word.includes(keyword.toLowerCase()) || keyword.toLowerCase().includes(word)
        )) {
          score += 3; // وزن أعلى للكلمات المفتاحية
        }
      }
      
      // البحث في الإجابة
      const answerWords = qaPair.answer.toLowerCase().split(/\s+/);
      const answerCommonWords = questionWords.filter(word => 
        answerWords.some(answerWord => 
          answerWord.includes(word) || word.includes(answerWord)
        )
      );
      score += answerCommonWords.length;
      
      if (score > 0 && (!bestMatch || score > bestMatch.score)) {
        bestMatch = { qaPair, score, category: category.category };
      }
    }
  }
  
  if (bestMatch && bestMatch.score >= 2) {
    console.log(`🎯 تم العثور على أفضل تطابق في ${bestMatch.category} (نقاط: ${bestMatch.score})`);
    return bestMatch.qaPair.answer;
  }
  
  return null;
}

/**
 * البحث باستخدام الذكاء الاصطناعي (Gemini مباشرة)
 */
async function searchWithAI(question: string): Promise<string | null> {
  try {
    // إعداد Gemini مباشرة
    const GEMINI_API_KEY = process.env.GEMINI_API_KEY || process.env.NEXT_PUBLIC_GEMINI_API_KEY;
    
    if (!GEMINI_API_KEY || GEMINI_API_KEY === 'your-gemini-api-key-here') {
      console.error('❌ مفتاح Gemini API غير موجود أو غير صحيح');
      console.error('❌ GEMINI_API_KEY:', GEMINI_API_KEY ? 'موجود' : 'غير موجود');
      
      // إجابات احتياطية للأسئلة الشائعة
      const questionLower = question.toLowerCase().trim();
      
      if (questionLower.includes('الطقس') || questionLower.includes('درجة الحرارة')) {
        return 'أعتذر، لا أستطيع الحصول على معلومات الطقس الحالية في الوقت الراهن. يرجى التحقق من تطبيق الطقس المحلي أو موقع الطقس للحصول على معلومات دقيقة.';
      }
      
      if (questionLower.includes('مرحبا') || questionLower.includes('السلام') || questionLower.includes('أهلا') || 
          questionLower.includes('السلام عليكم') || questionLower.includes('السلام عليك') || 
          questionLower.includes('أهلاً') || questionLower.includes('أهلا وسهلا') || 
          questionLower.includes('مرحباً') || questionLower.includes('مرحبا بك')) {
        return 'السلام عليكم! أهلاً وسهلاً بك. أنا SyriaGPT، كيف يمكنني مساعدتك اليوم؟';
      }
      
      if (questionLower.includes('كيف') && questionLower.includes('طبخ')) {
        return 'أعتذر، لا أستطيع تقديم وصفات طبخ مفصلة في الوقت الحالي. يرجى البحث عن وصفات الطبخ في المواقع المتخصصة أو الكتب المختصة.';
      }
      
      // إجابات احتياطية للأسئلة العامة الأخرى
      if (questionLower.includes('كود') || questionLower.includes('برمجة') || questionLower.includes('بايثون') || 
          questionLower.includes('جافا') || questionLower.includes('جافاسكريبت') || questionLower.includes('html') || 
          questionLower.includes('css') || questionLower.includes('sql') || questionLower.includes('خوارزمية')) {
        return 'أعتذر، لا أستطيع تقديم أكواد برمجية مفصلة في الوقت الحالي. يرجى البحث في المواقع المتخصصة بالبرمجة أو الكتب التعليمية.';
      }
      
      if (questionLower.includes('رياضيات') || questionLower.includes('حساب') || questionLower.includes('معادلة') || 
          questionLower.includes('جبر') || questionLower.includes('هندسة')) {
        return 'أعتذر، لا أستطيع حل المسائل الرياضية المعقدة في الوقت الحالي. يرجى استخدام الآلة الحاسبة أو البحث في المواقع المتخصصة بالرياضيات.';
      }
      
      if (questionLower.includes('طب') || questionLower.includes('دواء') || questionLower.includes('مرض') || 
          questionLower.includes('علاج') || questionLower.includes('صحة')) {
        return 'أعتذر، لا أستطيع تقديم نصائح طبية. يرجى استشارة طبيب مختص للحصول على المشورة الطبية المناسبة.';
      }
      
      // للأسئلة العامة الأخرى، حاول استخدام Gemini
      console.log('🔍 محاولة استخدام Gemini للأسئلة العامة...');
      try {
        const { GoogleGenerativeAI } = await import('@google/generative-ai');
        const genAI = new GoogleGenerativeAI(GEMINI_API_KEY);
        const model = genAI.getGenerativeModel({ 
          model: "gemini-1.5-flash",
          generationConfig: {
            temperature: 0.7,
            topK: 40,
            topP: 0.95,
            maxOutputTokens: 1024,
          },
        });
        
        const prompt = `أنت SyriaGPT، مساعد ذكي. أجب على السؤال التالي باللغة العربية بطريقة واضحة ومفيدة:
        
السؤال: ${question}

تعليمات:
- أجب باللغة العربية فقط
- كن دقيقاً ومفيداً
- قدم معلومات مفيدة ومفصلة
- تجنب الردود الطويلة جداً`;
        
        const result = await model.generateContent(prompt);
        const answer = result.response.text();
        
        if (answer && answer.trim().length > 5) {
          console.log('✅ تم الحصول على إجابة من Gemini للأسئلة العامة');
          return answer.trim();
        }
      } catch (geminiError: any) {
        console.error('❌ فشل Gemini للأسئلة العامة:', geminiError.message);
      }
      
      return 'أعتذر، لا أستطيع الإجابة على هذا السؤال في الوقت الحالي. يرجى إعادة صياغة السؤال أو طرح سؤال آخر.';
    }

    const { GoogleGenerativeAI } = await import('@google/generative-ai');
    const genAI = new GoogleGenerativeAI(GEMINI_API_KEY);
    const model = genAI.getGenerativeModel({
      model: "gemini-1.5-flash",
      generationConfig: {
        temperature: 0.3,
        topK: 40,
        topP: 0.8,
        maxOutputTokens: 1024,
      },
    });

    const prompt = `أنت SyriaGPT، مساعد ذكي متخصص في المعلومات السورية. أجب على السؤال التالي باللغة العربية بطريقة واضحة ومفيدة:

السؤال: ${question}

تعليمات:
- أجب باللغة العربية فقط
- كن دقيقاً ومفيداً
- إذا كان السؤال عن سوريا، قدم معلومات دقيقة
- إذا كان السؤال عاماً، قدم إجابة مفيدة
- تجنب الردود الطويلة جداً`;

    console.log('🤖 إرسال طلب إلى Gemini مباشرة...');
    const result = await model.generateContent(prompt);
    const response = await result.response;
    const answer = response.text();

    if (!answer || answer.trim().length < 5) {
      throw new Error('رد فارغ أو قصير جداً من Gemini');
    }

    console.log('✅ تم الحصول على إجابة من Gemini بنجاح');
    return answer.trim();
    
  } catch (error: any) {
    console.error('❌ فشل في الحصول على إجابة من Gemini:', error.message);
    
    // في حالة فشل Gemini، ارجع رد افتراضي مفيد
    const questionLower = question.toLowerCase().trim();
    
    if (questionLower.includes('طقس') || questionLower.includes('جو') || questionLower.includes('درجة الحرارة')) {
      return 'أعتذر، لا أستطيع توفير معلومات الطقس الحالية. يرجى التحقق من تطبيق الطقس المحلي أو موقع الطقس على الإنترنت.';
    }
    
    if (questionLower.includes('مرحبا') || questionLower.includes('السلام') || questionLower.includes('أهلا') || 
        questionLower.includes('السلام عليكم') || questionLower.includes('السلام عليك') || 
        questionLower.includes('أهلاً') || questionLower.includes('أهلا وسهلا') || 
        questionLower.includes('مرحباً') || questionLower.includes('مرحبا بك')) {
      return 'السلام عليكم! أهلاً وسهلاً بك. أنا SyriaGPT، كيف يمكنني مساعدتك اليوم؟';
    }
    
    if (questionLower.includes('طبخ') || questionLower.includes('طعام')) {
      return 'أعتذر، لا أستطيع توفير وصفات الطبخ في الوقت الحالي. يرجى البحث في مواقع الطبخ المتخصصة أو كتب الطبخ.';
    }
    
    // إجابات احتياطية للأسئلة العامة الأخرى
    if (questionLower.includes('كود') || questionLower.includes('برمجة') || questionLower.includes('بايثون') || 
        questionLower.includes('جافا') || questionLower.includes('جافاسكريبت') || questionLower.includes('html') || 
        questionLower.includes('css') || questionLower.includes('sql') || questionLower.includes('خوارزمية')) {
      return 'أعتذر، لا أستطيع تقديم أكواد برمجية مفصلة في الوقت الحالي. يرجى البحث في المواقع المتخصصة بالبرمجة أو الكتب التعليمية.';
    }
    
    if (questionLower.includes('رياضيات') || questionLower.includes('حساب') || questionLower.includes('معادلة') || 
        questionLower.includes('جبر') || questionLower.includes('هندسة')) {
      return 'أعتذر، لا أستطيع حل المسائل الرياضية المعقدة في الوقت الحالي. يرجى استخدام الآلة الحاسبة أو البحث في المواقع المتخصصة بالرياضيات.';
    }
    
    if (questionLower.includes('طب') || questionLower.includes('دواء') || questionLower.includes('مرض') || 
        questionLower.includes('علاج') || questionLower.includes('صحة')) {
      return 'أعتذر، لا أستطيع تقديم نصائح طبية. يرجى استشارة طبيب مختص للحصول على المشورة الطبية المناسبة.';
    }
    
    return 'أعتذر، لا أستطيع الإجابة على هذا السؤال في الوقت الحالي. يرجى إعادة صياغة السؤال أو طرح سؤال آخر.';
  }
}

/**
 * فحص أسئلة الهوية ومعلومات الشات
 */
function checkIdentityQuestion(question: string): string | null {
  const questionLower = question.toLowerCase().trim();
  
  // أنماط أسئلة الهوية
  const identityPatterns = [
    "من أنت", "من هو أنت", "من انت", "من هو انت", 
    "تعريف", "هويتك", "اسمك", "من أنت؟", "من انت؟",
    "من أنت بالضبط", "من انت بالضبط", "من أنت فعلاً", "من انت فعلاً",
    "من أنت حقيقة", "من انت حقيقة", "من أنت أساساً", "من انت اساساً",
    "من أنت بالتحديد", "من انت بالتحديد", "من أنت بالدقة", "من انت بالدقة",
    "من صانعك", "من طورك", "من برمجك", "من أنشأك", "من خلقك",
    "من قام بتطويرك", "من قام بإنشائك", "من قام ببرمجتك",
    "ما أنت", "ماذا أنت", "ما هو نوعك", "ما طبيعتك",
    "ماذا يمكنك أن تفعل", "ما يمكنك أن تفعل", "ماذا تستطيع أن تفعل",
    "ما هو هدفك", "ما هو غرضك", "ما هو مهمتك", "ما هو دورك"
  ];
  
  for (const pattern of identityPatterns) {
    if (questionLower.includes(pattern)) {
      return "أنا SyriaGPT، نموذج ذكاء اصطناعي تم تدريبي من قبل وكالة نظم المعلومات السورية. أنا متخصص في تقديم المعلومات الدقيقة والشاملة حول سوريا في جميع المجالات - التاريخ، الجغرافيا، الثقافة، الاقتصاد، والسياسة. هدفي هو مساعدتك في الحصول على معلومات موثوقة عن سوريا.";
    }
  }
  
  return null;
}

/**
 * فحص إذا كان السؤال متعلق بسوريا
 */
function isSyriaRelatedQuestion(question: string): boolean {
  const questionLower = question.toLowerCase().trim();
  
  // كلمات مفتاحية واضحة لسوريا
  const syriaKeywords = [
    "سوريا", "سوري", "سورية", "سوريين", "سوريات",
    "دمشق", "حلب", "حمص", "حماة", "اللاذقية", "دير الزور", "الرقة", "إدلب",
    "رئيس سوريا", "حكومة سوريا", "نظام سوريا", "دولة سوريا",
    "اقتصاد سوريا", "ثقافة سوريا", "تاريخ سوريا", "جغرافيا سوريا",
    "البنك المركزي السوري", "الليرة السورية", "العلم السوري",
    "البرلمان السوري", "الدستور السوري", "القانون السوري",
    "المدن السورية", "المحافظات السورية", "الجامعات السورية",
    "المطاعم السورية", "المطبخ السوري", "التراث السوري",
    "السياحة في سوريا", "المناخ في سوريا", "الزراعة في سوريا"
  ];
  
  // فحص وجود كلمات مفتاحية واضحة
  for (const keyword of syriaKeywords) {
    if (questionLower.includes(keyword)) {
      return true;
    }
  }
  
  return false;
}

/**
 * البحث الرئيسي - يتبع التسلسل الصحيح: هوية -> سوريا -> عام
 */
async function searchAnswer(question: string): Promise<string> {
  // 1. البحث في الكاش
  const cachedAnswer = searchInCache(question);
  if (cachedAnswer) {
    return cachedAnswer;
  }
  
  // 2. فحص أسئلة الهوية ومعلومات الشات أولاً
  const identityAnswer = checkIdentityQuestion(question);
  if (identityAnswer) {
    console.log('✅ تم اكتشاف سؤال هوية أو معلومات الشات');
    // حفظ في الكاش
    searchCache.set(question.toLowerCase().trim(), {
      answer: identityAnswer,
      timestamp: Date.now()
    });
    return identityAnswer;
  }
  
  // 3. فحص إذا كان السؤال متعلق بسوريا
  if (isSyriaRelatedQuestion(question)) {
    console.log('✅ تم اكتشاف سؤال متعلق بسوريا');
    
    // تحميل البيانات المحلية إذا لم تكن محملة
    if (!dataLoaded) {
      await loadLocalData();
    }
    
    // البحث في البيانات المحلية (أسئلة سوريا)
    let localAnswer = searchInLocalData(question);
    if (localAnswer) {
      console.log('✅ تم العثور على إجابة من بيانات سوريا المحلية');
      // حفظ في الكاش
      searchCache.set(question.toLowerCase().trim(), {
        answer: localAnswer,
        timestamp: Date.now()
      });
      return localAnswer;
    }
    
    // البحث المتقدم في البيانات المحلية
    localAnswer = advancedSearchInLocalData(question);
    if (localAnswer) {
      console.log('✅ تم العثور على إجابة متقدمة من بيانات سوريا المحلية');
      // حفظ في الكاش
      searchCache.set(question.toLowerCase().trim(), {
        answer: localAnswer,
        timestamp: Date.now()
      });
      return localAnswer;
    }
    
    // إذا لم نجد إجابة في البيانات المحلية لسؤال سوري
    console.log('❌ لم يتم العثور على إجابة في بيانات سوريا المحلية');
    return 'أعتذر، لا أستطيع العثور على معلومات كافية حول هذا الموضوع السوري في قاعدة البيانات المحلية.';
  }
  
  // 4. الأسئلة العامة - استخدام Gemini مباشرة
  console.log('🔍 سؤال عام، استخدام Gemini مباشرة');
  try {
    const aiAnswer = await searchWithAI(question);
    if (aiAnswer && aiAnswer.trim().length > 5) {
      console.log('✅ تم الحصول على إجابة من Gemini للأسئلة العامة');
      // حفظ في الكاش
      searchCache.set(question.toLowerCase().trim(), {
        answer: aiAnswer,
        timestamp: Date.now()
      });
      return aiAnswer;
    } else {
      console.log('❌ Gemini لم يعط إجابة صحيحة');
    }
  } catch (error: any) {
    console.error('❌ خطأ في Gemini:', error.message);
  }
  
  // 5. رد افتراضي
  return 'أعتذر، لم أتمكن من العثور على إجابة مناسبة لسؤالك. هل يمكنك إعادة صياغة السؤال؟';
}

export async function POST(request: NextRequest) {
  try {
    const { question } = await request.json();

    if (!question || typeof question !== 'string' || question.trim() === '') {
      return NextResponse.json({ error: 'يرجى إدخال سؤال صحيح.' }, { status: 400 });
    }

    const answer = await searchAnswer(question.trim());

    return NextResponse.json({
      answer,
      timestamp: new Date().toISOString(),
      source: 'search_service'
    });

  } catch (error: any) {
    console.error('💥 خطأ في خدمة البحث:', error);
    return NextResponse.json({
      answer: 'أعتذر، حدث خطأ غير متوقع. فريقنا يعمل على إصلاحه. الرجاء المحاولة مرة أخرى بعد قليل.',
      timestamp: new Date().toISOString(),
      source: 'error'
    }, { status: 500 });
  }
}

// إضافة endpoint لاختبار Gemini
export async function GET() {
  try {
    // اختبار Gemini مباشرة
    const testQuestion = "ما هو الطقس اليوم؟";
    const geminiAnswer = await searchWithAI(testQuestion);
    
    // فحص متغيرات البيئة
    const envCheck = {
      GEMINI_API_KEY: process.env.GEMINI_API_KEY ? 'موجود' : 'غير موجود',
      NEXT_PUBLIC_GEMINI_API_KEY: process.env.NEXT_PUBLIC_GEMINI_API_KEY ? 'موجود' : 'غير موجود',
      GEMINI_API_KEY_VALUE: process.env.GEMINI_API_KEY || 'غير موجود',
    };
    
    return NextResponse.json({
      message: 'SyriaGPT Search API - v1.0',
      status: 'active',
      environment_check: envCheck,
      gemini_test: {
        question: testQuestion,
        answer: geminiAnswer,
        working: !!geminiAnswer
      },
      timestamp: new Date().toISOString(),
    });
  } catch (error: any) {
    return NextResponse.json({
      message: 'SyriaGPT Search API - v1.0',
      status: 'error',
      error: error.message,
      timestamp: new Date().toISOString(),
    });
  }
}
