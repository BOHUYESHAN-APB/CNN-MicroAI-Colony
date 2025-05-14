import { i18n as I18nInterface } from 'i18next';

declare module '@jest/globals' {
  export const jest: {
    fn: () => jest.Mock;
    clearAllMocks: () => void;
  };
}

declare module 'i18next' {
  export interface i18n extends I18nInterface {
    t: jest.Mock;
    changeLanguage: (lang: string) => Promise<Function>;
    language: string;
  }
}

declare module 'react-i18next' {
  export const initReactI18next: {
    type: string;
    init: (instance: i18n) => void;
  };
  
  export interface UseTranslationResponse {
    t: jest.Mock;
    i18n: i18n;
    ready: boolean;
  }
  
  export function useTranslation(): UseTranslationResponse;
}

export interface MockTranslations {
  'zh-CN': {
    common: {
      save: string;
      cancel: string;
      confirm: string;
    };
    settings: {
      camera: {
        title: string;
        resolution: string;
        fps: string;
      };
    };
  };
  'en-US': {
    common: {
      save: string;
      cancel: string;
      confirm: string;
    };
    settings: {
      camera: {
        title: string;
        resolution: string;
        fps: string;
      };
    };
  };
}

export type LanguageCode = 'zh-CN' | 'en-US';

export interface I18nTestUtils {
  changeLanguage: (lang: LanguageCode) => Promise<Function>;
  getCurrentLanguage: () => string;
  translate: (key: string, lang?: LanguageCode) => string;
  mockTranslation: (key: string, value: string, lang?: LanguageCode) => jest.Mock;
  clearMocks: () => void;
  i18n: i18n;
}
