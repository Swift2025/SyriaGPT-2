// i18n-config.ts

export const i18n = {
  defaultLocale: 'en',
  locales: [
    'am', 'ar', 'az', 'bg', 'bn', 'ca', 'cs', 'da', 'de', 'el', 
    'en', 'es', 'fa', 'fi', 'fr', 'gu', 'ha', 'he', 'hi', 'hu', 
    'hy', 'id', 'it', 'ja', 'ka', 'kn', 'ko', 'mr', 'ms', 'nl', 
    'no', 'pa', 'pl', 'pt', 'ro', 'ru', 'sq', 'sr', 'sv', 'sw', 
    'ta', 'te', 'th', 'tl', 'tr', 'uk', 'ur', 'vi', 'yo', 'zh'
  ],
} as const;

export type Locale = (typeof i18n)['locales'][number];