/// <reference types="@testing-library/jest-dom" />
/// <reference types="@jest/globals" />

import { jest, describe, it, expect, beforeEach, afterEach } from '@jest/globals';
import type { RenderHookResult } from '@testing-library/react-hooks';
import type { UseTranslationResponse } from 'react-i18next';

declare global {
  // Extend the Jest namespace
  namespace jest {
    interface Mock<T = any, Y extends any[] = any> {
      mockClear: () => void;
      mockReset: () => void;
      mockImplementation: (fn: (...args: Y) => T) => this;
      mockReturnValue: (value: T) => this;
    }
  }

  // Translation Types
  interface I18nInstance {
    language: string;
    changeLanguage: (lang: string) => Promise<Function>;
    t: jest.Mock;
  }

  interface TranslationHook extends UseTranslationResponse {
    i18n: I18nInstance;
  }

  // Testing Library Types
  type RenderHookOptions<P> = {
    initialProps?: P;
    wrapper?: React.ComponentType<any>;
  };

  interface CustomMatchers<R = unknown> {
    toBeInTheDocument(): R;
    toHaveStyle(style: Record<string, any>): R;
  }

  namespace jest {
    interface Expect extends CustomMatchers {}
    interface Matchers<R> extends CustomMatchers<R> {}
    interface InverseAsymmetricMatchers extends CustomMatchers {}
  }
}

export {
  jest,
  describe,
  it,
  expect,
  beforeEach,
  afterEach,
  RenderHookResult,
  UseTranslationResponse
};
