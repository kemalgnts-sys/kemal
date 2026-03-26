import { I18n } from 'i18n-js';
import * as Localization from 'expo-localization';
import { translations } from './translations';

const i18n = new I18n(translations);

// Set the locale once at the beginning of your app
i18n.locale = Localization.locale.split('-')[0];

// Fallback to English if translation is missing
i18n.enableFallback = true;
i18n.defaultLocale = 'en';

export const setLanguage = (lang) => {
  i18n.locale = lang;
};

export const getLanguage = () => i18n.locale;

export const t = (key, options) => i18n.t(key, options);

export const availableLanguages = [
  { code: 'en', name: 'English', flag: '🇺🇸' },
  { code: 'es', name: 'Español', flag: '🇪🇸' },
  { code: 'tr', name: 'Türkçe', flag: '🇹🇷' },
];

export default i18n;
