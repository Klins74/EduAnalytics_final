import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import translationRU from './locales/ru/translation.json';
import translationKZ from './locales/kz/translation.json';
import translationEN from './locales/en/translation.json';

i18n
  .use(initReactI18next)
  .init({
    resources: {
      ru: { translation: translationRU },
      kz: { translation: translationKZ },
      en: { translation: translationEN }
    },
    lng: 'ru',
    fallbackLng: 'ru',
    interpolation: { escapeValue: false }
  });

export default i18n;