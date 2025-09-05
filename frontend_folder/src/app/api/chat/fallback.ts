// src/app/api/chat/fallback.ts

// تعريف بسيط لأنواع الرسائل لتجنب الأخطاء
interface Message {
  sender: 'user' | 'bot';
  content: string;
}

// قاموس للمدن السورية ومعلوماتها الأساسية
const SYRIAN_CITIES = {
  دمشق: {
    nickname: 'العاصمة',
    population: '2.5 مليون نسمة',
    famous: 'الجامع الأموي، البلد القديمة'
  },
  حلب: {
    nickname: 'الشهباء',
    population: '2.1 مليون نسمة', 
    famous: 'القلعة، السوق المسقوف'
  },
  حمص: {
    nickname: 'أم العمود الأسود',
    population: '775 ألف نسمة',
    famous: 'قلعة حمص، كنيسة أم الزنار'
  },
  حماة: {
    nickname: 'مدينة النواعير',
    population: '410 آلاف نسمة',
    famous: 'النواعير، قصر العظم'
  },
  اللاذقية: {
    nickname: 'عروس الشاطئ',
    population: '650 ألف نسمة',
    famous: 'الشاطئ، القلعة الصليبية'
  }
};

// وصفات الطبخ السوري الشعبية
const RECIPES = {
  كبة: {
    ingredients: ['برغل ناعم', 'لحم مفروم', 'بصل', 'بهارات', 'صنوبر'],
    steps: [
      'انقع البرغل وصفه جيداً',
      'اعجن البرغل مع اللحم والبصل والبهارات',
      'شكل كرات واحشها باللحم والصنوبر',
      'اقلها في زيت حار حتى تحمر'
    ],
    tips: 'أضف قليلاً من دبس الرمان للحشوة'
  },
  محشي: {
    ingredients: ['ورق عنب', 'أرز', 'لحم مفروم', 'طماطم', 'بقدونس', 'نعناع'],
    steps: [
      'اخلط الأرز مع اللحم والخضار',
      'لف الخليط في ورق العنب',
      'رص القطع في القدر',
      'اطبخها بالمرق على نار هادئة'
    ],
    tips: 'ضع طبقاً مقلوباً في القدر لمنع الالتصاق'
  },
  فتوش: {
    ingredients: ['خبز محمص', 'خضار مشكلة', 'رمان', 'سماق', 'ليمون', 'زيت زيتون'],
    steps: [
      'قطع الخضار قطع صغيرة',
      'حمص الخبز وكسره',
      'اخلط كل المكونات',
      'أضف الصلصة والسماق'
    ],
    tips: 'لا تضع الخبز إلا قبل التقديم مباشرة'
  }
};

// معلومات التراث السوري
const HERITAGE = {
  الحرف: {
    الدمشقي: 'التطعيم بالصدف والذهب، الحرير الطبيعي',
    الحلبي: 'الصابون الغار، المنسوجات',
    الحموي: 'الخزف، الفخار',
    الحمصي: 'الزجاج المنفوخ، المعادن'
  },
  الرقص: {
    الدبكة: 'رقص شعبي جماعي',
    السماح: 'رقص صوفي',
    العتابا: 'غناء تراثي مع حركات'
  },
  الآلات: {
    العود: 'آلة الموسيقى السورية الأساسية',
    القانون: 'آلة وترية تراثية',
    الناي: 'آلة نفخ خشبية',
    الدف: 'آلة إيقاعية'
  }
};

/**
 * نظام احتياطي متطور للإجابة على الأسئلة حول سوريا
 * @param message - رسالة المستخدم
 * @param history - تاريخ المحادثة
 * @returns رد تفصيلي
 */
export async function getAdvancedFallback(message: string, history: Message[] = []): Promise<string> {
  const lowerMessage = message.toLowerCase().trim();
  
  // تحليل السياق من المحادثة السابقة
  const lastBotMessage = history.slice().reverse().find(msg => msg.sender === 'bot');
  const contextKeywords = lastBotMessage ? lastBotMessage.content.toLowerCase() : '';

  // === المدن السورية ===
  for (const [city, info] of Object.entries(SYRIAN_CITIES)) {
    if (lowerMessage.includes(city)) {
      if (lowerMessage.includes('سكان') || lowerMessage.includes('عدد')) {
        return `سكان ${city}: ${info.population}\n\n${city} تُعرف باسم "${info.nickname}" وتشتهر بـ ${info.famous}.\n\nهل تريد معرفة المزيد عن أحياء أو معالم ${city}؟`;
      }
      if (lowerMessage.includes('معالم') || lowerMessage.includes('أماكن') || lowerMessage.includes('زيارة')) {
        return getCityAttractions(city);
      }
      if (lowerMessage.includes('طعام') || lowerMessage.includes('أكل') || lowerMessage.includes('مطاعم')) {
        return getCityFood(city);
      }
      if (lowerMessage.includes('تاريخ')) {
        return getCityHistory(city);
      }
    }
  }

  // === الطبخ والوصفات ===
  for (const [dish, recipe] of Object.entries(RECIPES)) {
    if (lowerMessage.includes(dish)) {
      if (lowerMessage.includes('وصفة') || lowerMessage.includes('طبخ') || lowerMessage.includes('عمل')) {
        return formatRecipe(dish, recipe);
      }
    }
  }

  // === التراث والثقافة ===
  if (lowerMessage.includes('تراث') || lowerMessage.includes('ثقافة')) {
    if (lowerMessage.includes('حرف') || lowerMessage.includes('صناعة')) {
      return getHeritageInfo('الحرف');
    }
    if (lowerMessage.includes('رقص') || lowerMessage.includes('دبكة')) {
      return getHeritageInfo('الرقص');
    }
    if (lowerMessage.includes('موسيقى') || lowerMessage.includes('آلات')) {
      return getHeritageInfo('الآلات');
    }
    return getGeneralHeritage();
  }

  // === التعليم والجامعات ===
  if (lowerMessage.includes('جامعة') || lowerMessage.includes('تعليم') || lowerMessage.includes('دراسة')) {
    return getEducationInfo(lowerMessage);
  }

  // === الطقس والجغرافيا ===
  if (lowerMessage.includes('طقس') || lowerMessage.includes('مناخ') || lowerMessage.includes('جبال')) {
    return getGeographyInfo(lowerMessage);
  }

  // === اللغة واللهجة ===
  if (lowerMessage.includes('لهجة') || lowerMessage.includes('لغة') || lowerMessage.includes('كلمات')) {
    return getDialectInfo(lowerMessage);
  }

  // === الاقتصاد والعمل ===
  if (lowerMessage.includes('اقتصاد') || lowerMessage.includes('عمل') || lowerMessage.includes('صناعة')) {
    return getEconomyInfo(lowerMessage);
  }

  // === المواصلات ===
  if (lowerMessage.includes('مواصلات') || lowerMessage.includes('نقل') || lowerMessage.includes('سفر')) {
    return getTransportInfo(lowerMessage);
  }

  // === الأحداث التاريخية المهمة ===
  if (lowerMessage.includes('تاريخ') || lowerMessage.includes('الاستقلال') || lowerMessage.includes('أموي')) {
    return getHistoricalInfo(lowerMessage);
  }

  // === العادات والتقاليد ===
  if (lowerMessage.includes('عادات') || lowerMessage.includes('تقاليد') || lowerMessage.includes('أعياد')) {
    return getTraditionsInfo(lowerMessage);
  }

  // === رد عام ذكي ===
  return getSmartGeneralResponse(message);
}

// دوال مساعدة للمدن
function getCityAttractions(city: string): string {
  const attractions: { [key: string]: string[] } = {
    دمشق: ['الجامع الأموي', 'قلعة دمشق', 'البلد القديمة', 'سوق الحميدية', 'جبل قاسيون'],
    حلب: ['قلعة حلب', 'السوق القديم', 'الجامع الكبير', 'بيت جبري', 'حي الفرافرة'],
    حمص: ['قلعة حمص', 'كنيسة أم الزنار', 'جامع خالد بن الوليد', 'البلد القديمة'],
    حماة: ['النواعير', 'قصر العظم', 'جامع الحسين', 'البلد القديمة'],
    اللاذقية: ['الكورنيش', 'القلعة الصليبية', 'المسرح الروماني', 'شاطئ الشاموس']
  };

  const cityAttractions = attractions[city] || ['معالم متنوعة'];
  return `أجمل معالم ${city}:\n\n${cityAttractions.map((attraction, index) => 
    `${index + 1}. ${attraction}`
  ).join('\n')}\n\nهل تريد تفاصيل عن أي من هذه المعالم؟`;
}

function getCityFood(city: string): string {
  const foods: { [key: string]: { dishes: string[], restaurants: string[] } } = {
    دمشق: {
      dishes: ['الكبة الشامية', 'الفتة الشامية', 'المحاشي'],
      restaurants: ['مطعم الخواجة', 'بيت جبري', 'أم شريف']
    },
    حلب: {
      dishes: ['الكبة الحلبية', 'الشاورما الحلبية', 'المعمول'],
      restaurants: ['مطعم بيت سيسي', 'الأندلسي', 'كراج الشاورما']
    }
  };

  const cityFood = foods[city];
  if (cityFood) {
    return `أشهر أطباق ${city}:\n\n${cityFood.dishes.map(dish => `• ${dish}`).join('\n')}\n\nمطاعم مشهورة:\n${cityFood.restaurants.map(restaurant => `• ${restaurant}`).join('\n')}\n\nهل تريد وصفة لطبق معين؟`;
  }
  return `${city} تشتهر بمأكولات متنوعة ولذيذة. هل تريد معرفة طبق معين؟`;
}

function getCityHistory(city: string): string {
  const histories: { [key: string]: string } = {
    دمشق: 'دمشق من أقدم مدن العالم المأهولة بالسكان، يعود تاريخها إلى الألف السابع قبل الميلاد. كانت عاصمة للدولة الأموية، وتُعتبر مهد الحضارة العربية الإسلامية.',
    حلب: 'حلب مدينة تاريخية عريقة، كانت محطة مهمة على طريق الحرير. تضم قلعة من أعظم القلاع في العالم وسوقاً مسقوفاً يُعد الأطول عالمياً.',
    حمص: 'حمص مدينة تاريخية تُعرف بأم العمود الأسود، لها دور مهم في التاريخ الإسلامي وتضم مقام الصحابي خالد بن الوليد.',
    حماة: 'حماة تشتهر بالنواعير التاريخية التي تُعد من أقدم آلات رفع المياه في العالم، وكانت مركزاً مهماً للري والزراعة.'
  };

  return histories[city] || `${city} لها تاريخ عريق وحضارة أصيلة تمتد لقرون عديدة.`;
}

// دوال التراث والثقافة
function getHeritageInfo(category: keyof typeof HERITAGE): string {
  const info = HERITAGE[category];
  let response = `التراث السوري - ${category}:\n\n`;
  
  for (const [key, value] of Object.entries(info)) {
    response += `${key}: ${value}\n`;
  }
  
  return response + '\nهل تريد معرفة تفاصيل أكثر عن أي من هذه العناصر؟';
}

function getGeneralHeritage(): string {
  return `التراث السوري غني ومتنوع يشمل:\n\n• الحرف اليدوية التقليدية\n• الموسيقى والرقص الشعبي\n• العادات والتقاليد\n• الطبخ الأصيل\n• العمارة التراثية\n\nأي جانب من التراث يهمك أكثر؟`;
}

// دوال المعلومات المتخصصة
function getEducationInfo(message: string): string {
  if (message.includes('دمشق')) {
    return `جامعة دمشق - أعرق الجامعات السورية:\n\n• تأسست عام 1923\n• تضم كليات الطب والهندسة والحقوق والآداب\n• المدينة الجامعية في المزة\n• تخرج منها علماء ومفكرون مرموقون\n\nهل تريد معلومات عن كلية معينة؟`;
  }
  if (message.includes('حلب')) {
    return `جامعة حلب:\n\n• تأسست عام 1958\n• تشتهر بكليات الهندسة والطب\n• لها فروع في عدة محافظات\n• مركز مهم للبحث العلمي\n\nما التخصص الذي يهمك؟`;
  }
  return `النظام التعليمي في سوريا يشمل:\n\n• التعليم الأساسي (9 سنوات)\n• التعليم الثانوي (3 سنوات)\n• التعليم الجامعي والعالي\n• معاهد تقنية ومهنية متخصصة\n\nأي مرحلة تعليمية تهمك؟`;
}

function getGeographyInfo(message: string): string {
  if (message.includes('جبال')) {
    return `الجبال في سوريا:\n\n• جبال طوروس (شمال)\n• جبل الشيخ (حرمون)\n• الجبال الساحلية (غرب)\n• جبال القلمون (وسط)\n• جبل العرب (جنوب)\n\nكل منطقة لها مناخها وطبيعتها الخاصة.`;
  }
  if (message.includes('مناخ') || message.includes('طقس')) {
    return `مناخ سوريا متوسطي معتدل:\n\n• صيف حار وجاف\n• شتاء بارد وماطر\n• الساحل أكثر اعتدالاً\n• الداخل أكثر جفافاً وبرودة شتاءً\n• أفضل أوقات الزيارة: الربيع والخريف`;
  }
  return `جغرافية سوريا متنوعة: ساحل على المتوسط، جبال، سهول، وبادية في الشرق.`;
}

function getDialectInfo(message: string): string {
  const syrianWords = [
    'شو: ماذا',
    'وين: أين',
    'هيك: هكذا',
    'مبارح: أمس',
    'بكرا: غداً',
    'عنجد: حقاً',
    'يلا: هيا بنا'
  ];

  return `اللهجة السورية متميزة وجميلة:\n\n${syrianWords.join('\n')}\n\nكل منطقة لها لكنتها الخاصة، لكن الكل يفهم بعضه البعض!\n\nهل تريد تعلم كلمات أخرى؟`;
}

function getEconomyInfo(message: string): string {
  return `الاقتصاد السوري تقليدياً يعتمد على:\n\n• الزراعة (قطن، قمح، زيتون)\n• الصناعة (نسيج، غذائية، كيماوية)\n• السياحة\n• التجارة\n• الخدمات\n\nسوريا لديها موارد طبيعية وبشرية مهمة.`;
}

function getTransportInfo(message: string): string {
  return `وسائل النقل في سوريا:\n\n• الباصات العامة\n• المايكروباصات (السرافيس)\n• التكاسي\n• القطارات (خطوط محدودة)\n• الطيران المحلي\n\nدمشق وحلب لديهما شبكات نقل متطورة نسبياً.`;
}

function getHistoricalInfo(message: string): string {
  if (message.includes('استقلال')) {
    return `استقلال سوريا:\n\n• الاستقلال عن فرنسا: 17 أبريل 1946\n• يوم الجلاء: عيد وطني\n• نضال طويل ضد الانتداب\n• شخصيات مهمة: شكري القوتلي، سعد الله الجابري\n\nيوم فخر لكل السوريين!`;
  }
  if (message.includes('أموي')) {
    return `الدولة الأموية (661-750م):\n\n• العاصمة: دمشق\n• أول دولة إسلامية وراثية\n• امتدت من الأندلس إلى آسيا الوسطى\n• الجامع الأموي في دمشق تحفة معمارية\n• عصر ذهبي للحضارة الإسلامية`;
  }
  return `تاريخ سوريا عريق يمتد لآلاف السنين، من الحضارات القديمة إلى العصر الإسلامي والحديث.`;
}

function getTraditionsInfo(message: string): string {
  if (message.includes('أعياد')) {
    return `الأعياد في سوريا:\n\n• عيد الفطر والأضحى\n• رأس السنة الميلادية والهجرية\n• عيد الاستقلال (17 أبريل)\n• عيد المولد النبوي\n• أعياد دينية مسيحية\n\nكل عيد له طقوسه وأطباقه الخاصة!`;
  }
  return `العادات السورية الأصيلة:\n\n• الكرم وحسن الضيافة\n• الاحترام للكبار\n• التجمعات العائلية\n• القهوة السادة رمز الضيافة\n• الدبكة في المناسبات\n• العزائم والولائم\n\nالسوريون معروفون بطيبة القلب والكرم.`;
}

// دالة تنسيق الوصفات
function formatRecipe(dishName: string, recipe: any): string {
  return `وصفة ${dishName} الأصلية:\n\nالمكونات:\n${recipe.ingredients.map((ing: string) => `• ${ing}`).join('\n')}\n\nطريقة التحضير:\n${recipe.steps.map((step: string, index: number) => `${index + 1}. ${step}`).join('\n')}\n\nنصيحة المطبخ: ${recipe.tips}\n\nبالهناء والشفاء!`;
}

// رد عام ذكي
function getSmartGeneralResponse(message: string): string {
  const responses = [
    `أفهم اهتمامك بـ "${message}".\n\nكمساعد متخصص في الشؤون السورية، يمكنني مساعدتك في:\n\n• معلومات عن المدن والمحافظات\n• الطبخ السوري والوصفات\n• التاريخ والتراث\n• التعليم والثقافة\n• الجغرافيا والمناخ\n\nهل يمكنك توضيح ما تريد معرفته بالضبط؟`,
    
    `سؤالك عن "${message}" مهم!\n\nأستطيع تقديم معلومات شاملة عن:\n\n• الحياة في سوريا\n• السياحة والمعالم\n• العادات والتقاليد\n• اللغة واللهجات\n• التاريخ العريق\n\nما الجانب الذي يثير اهتمامك أكثر؟`,
    
    `"${message}" موضوع شيق!\n\nبإمكاني مشاركة معرفتي حول:\n\n• التراث السوري الأصيل\n• المأكولات الشعبية\n• المدن التاريخية\n• الثقافة والفنون\n• الحياة الاجتماعية\n\nأي من هذه المواضيع تفضل أن نتحدث عنه؟`
  ];

  return responses[Math.floor(Math.random() * responses.length)];
}