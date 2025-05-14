import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import { jest } from '@jest/globals';

// Mock translations
const mockTranslations = {
  'zh-CN': {
    common: {
      save: '保存',
      cancel: '取消',
      confirm: '确认'
    },
    settings: {
      camera: {
        title: '相机设置',
        resolution: '分辨率',
        fps: '帧率'
      }
    }
  },
  'en-US': {
    common: {
      save: 'Save',
      cancel: 'Cancel',
      confirm: 'Confirm'
    },
    settings: {
      camera: {
        title: 'Camera Settings',
        resolution: 'Resolution',
        fps: 'Frame Rate'
      }
    }
  }
};

// Initialize i18n instance for testing
i18n
  .use(initReactI18next)
  .init({
    resources: mockTranslations,
    lng: 'zh-CN',
    fallbackLng: 'en-US',
    interpolation: {
      escapeValue: false
    }
  });

// Helper functions for testing
export const changeLanguage = (lang: 'zh-CN' | 'en-US') => {
  return i18n.changeLanguage(lang);
};

export const getCurrentLanguage = () => {
  return i18n.language;
};

export const translate = (key: string, lang?: 'zh-CN' | 'en-US') => {
  if (lang) {
    i18n.changeLanguage(lang);
  }
  return i18n.t(key);
};

// Jest helper for mocking translations
export const mockTranslation = (key: string, value: string, lang?: 'zh-CN' | 'en-US') => {
  const mockT = jest.fn();
  mockT.mockReturnValue(value);
  i18n.t = mockT;
  if (lang) {
    i18n.changeLanguage(lang);
  }
  return mockT;
};

export const clearMocks = () => {
  jest.clearAllMocks();
  i18n.changeLanguage('zh-CN');
};

// Types for testing
export type TestTranslationKey = keyof typeof mockTranslations['zh-CN'] | 
  keyof typeof mockTranslations['en-US'];

export { i18n };
