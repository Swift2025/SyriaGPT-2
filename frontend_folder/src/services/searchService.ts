// src/services/searchService.ts

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
        const response = await fetch(`/data/syria_knowledge/${file}`);
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
  
  for (const category of localData) {
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
 * البحث باستخدام الذكاء الاصطناعي
 */
async function searchWithAI(question: string): Promise<string | null> {
  try {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: question,
        conversationHistory: []
      }),
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    console.log('🤖 تم الحصول على إجابة من الذكاء الاصطناعي');
    return data.message || null;
  } catch (error) {
    console.error('❌ فشل في الحصول على إجابة من الذكاء الاصطناعي:', error);
    return null;
  }
}

/**
 * البحث الرئيسي - يتبع التسلسل المطلوب
 */
export async function searchAnswer(question: string): Promise<string> {
  // 1. البحث في الكاش
  const cachedAnswer = searchInCache(question);
  if (cachedAnswer) {
    return cachedAnswer;
  }
  
  // 2. تحميل البيانات المحلية إذا لم تكن محملة
  if (!dataLoaded) {
    await loadLocalData();
  }
  
  // 3. البحث في البيانات المحلية (بحث دقيق أولاً)
  let localAnswer = searchInLocalData(question);
  if (localAnswer) {
    // حفظ في الكاش
    searchCache.set(question.toLowerCase().trim(), {
      answer: localAnswer,
      timestamp: Date.now()
    });
    return localAnswer;
  }
  
  // 4. البحث المتقدم في البيانات المحلية
  localAnswer = advancedSearchInLocalData(question);
  if (localAnswer) {
    // حفظ في الكاش
    searchCache.set(question.toLowerCase().trim(), {
      answer: localAnswer,
      timestamp: Date.now()
    });
    return localAnswer;
  }
  
  // 5. البحث باستخدام الذكاء الاصطناعي
  const aiAnswer = await searchWithAI(question);
  if (aiAnswer) {
    // حفظ في الكاش
    searchCache.set(question.toLowerCase().trim(), {
      answer: aiAnswer,
      timestamp: Date.now()
    });
    return aiAnswer;
  }
  
  // 6. رد افتراضي
  return 'أعتذر، لم أتمكن من العثور على إجابة مناسبة لسؤالك. هل يمكنك إعادة صياغة السؤال؟';
}

/**
 * مسح الكاش
 */
export function clearCache(): void {
  searchCache.clear();
  console.log('🗑️ تم مسح الكاش');
}

/**
 * إحصائيات الكاش
 */
export function getCacheStats(): { size: number; entries: string[] } {
  return {
    size: searchCache.size,
    entries: Array.from(searchCache.keys())
  };
}
