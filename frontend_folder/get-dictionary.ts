// get-dictionary.ts
import type { Locale } from './i18n-config';

// تعريف قاموس يربط كل رمز لغة بملف الترجمة الخاص به
const dictionaries = {
  am: () => import('./dictionaries/am.json').then((module) => module.default),
  ar: () => import('./dictionaries/ar.json').then((module) => module.default),
  az: () => import('./dictionaries/az.json').then((module) => module.default),
  bg: () => import('./dictionaries/bg.json').then((module) => module.default),
  bn: () => import('./dictionaries/bn.json').then((module) => module.default),
  ca: () => import('./dictionaries/ca.json').then((module) => module.default),
  cs: () => import('./dictionaries/cs.json').then((module) => module.default),
  da: () => import('./dictionaries/da.json').then((module) => module.default),
  de: () => import('./dictionaries/de.json').then((module) => module.default),
  el: () => import('./dictionaries/el.json').then((module) => module.default),
  en: () => import('./dictionaries/en.json').then((module) => module.default),
  es: () => import('./dictionaries/es.json').then((module) => module.default),
  fa: () => import('./dictionaries/fa.json').then((module) => module.default),
  fi: () => import('./dictionaries/fi.json').then((module) => module.default),
  fr: () => import('./dictionaries/fr.json').then((module) => module.default),
  gu: () => import('./dictionaries/gu.json').then((module) => module.default),
  ha: () => import('./dictionaries/ha.json').then((module) => module.default),
  he: () => import('./dictionaries/he.json').then((module) => module.default),
  hi: () => import('./dictionaries/hi.json').then((module) => module.default),
  hu: () => import('./dictionaries/hu.json').then((module) => module.default),
  hy: () => import('./dictionaries/hy.json').then((module) => module.default),
  id: () => import('./dictionaries/id.json').then((module) => module.default),
  it: () => import('./dictionaries/it.json').then((module) => module.default),
  ja: () => import('./dictionaries/ja.json').then((module) => module.default),
  ka: () => import('./dictionaries/ka.json').then((module) => module.default),
  kn: () => import('./dictionaries/kn.json').then((module) => module.default),
  ko: () => import('./dictionaries/ko.json').then((module) => module.default),
  mr: () => import('./dictionaries/mr.json').then((module) => module.default),
  ms: () => import('./dictionaries/ms.json').then((module) => module.default),
  nl: () => import('./dictionaries/nl.json').then((module) => module.default),
  no: () => import('./dictionaries/no.json').then((module) => module.default),
  pa: () => import('./dictionaries/pa.json').then((module) => module.default),
  pl: () => import('./dictionaries/pl.json').then((module) => module.default),
  pt: () => import('./dictionaries/pt.json').then((module) => module.default),
  ro: () => import('./dictionaries/ro.json').then((module) => module.default),
  ru: () => import('./dictionaries/ru.json').then((module) => module.default),
  sq: () => import('./dictionaries/sq.json').then((module) => module.default),
  sr: () => import('./dictionaries/sr.json').then((module) => module.default),
  sv: () => import('./dictionaries/sv.json').then((module) => module.default),
  sw: () => import('./dictionaries/sw.json').then((module) => module.default),
  ta: () => import('./dictionaries/ta.json').then((module) => module.default),
  te: () => import('./dictionaries/te.json').then((module) => module.default),
  th: () => import('./dictionaries/th.json').then((module) => module.default),
  tl: () => import('./dictionaries/tl.json').then((module) => module.default),
  tr: () => import('./dictionaries/tr.json').then((module) => module.default),
  uk: () => import('./dictionaries/uk.json').then((module) => module.default),
  ur: () => import('./dictionaries/ur.json').then((module) => module.default),
  vi: () => import('./dictionaries/vi.json').then((module) => module.default),
  yo: () => import('./dictionaries/yo.json').then((module) => module.default),
  zh: () => import('./dictionaries/zh.json').then((module) => module.default),
};

// هذه الدالة ستبقى كما هي، لكنها الآن ستعمل مع كل اللغات الجديدة
export const getDictionary = async (locale: Locale) => {
  // التأكد من أن اللغة المطلوبة موجودة، وإلا استخدم اللغة الافتراضية
  const loader = dictionaries[locale] || dictionaries.en;
  return loader();
};