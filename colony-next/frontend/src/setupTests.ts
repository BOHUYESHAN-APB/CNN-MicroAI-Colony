import '@testing-library/jest-dom';
import { configure } from '@testing-library/react';
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import { server } from './mocks/server';

// Setup MSW
beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

// Configure testing library
configure({
  testIdAttribute: 'data-testid',
  asyncUtilTimeout: 2000,
});

// Setup i18n for testing
i18n
  .use(initReactI18next)
  .init({
    resources: {
      'zh-CN': {
        translation: require('./i18n/locales/zh-CN.json')
      },
      'en-US': {
        translation: require('./i18n/locales/en-US.json')
      }
    },
    lng: 'zh-CN', // Default language for tests
    fallbackLng: 'en-US',
    interpolation: {
      escapeValue: false
    },
    react: {
      useSuspense: false
    }
  });

// Global test utilities
global.sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(),
    removeListener: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
  observe = jest.fn();
  unobserve = jest.fn();
  disconnect = jest.fn();
};

// Mock IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
  observe = jest.fn();
  unobserve = jest.fn();
  disconnect = jest.fn();
  root = null;
  rootMargin = '';
  thresholds = [];
};

// Mock fetch
global.fetch = jest.fn();

// Custom error handler for React 18
const originalError = console.error;
console.error = (...args) => {
  if (/Warning.*not wrapped in act/.test(args[0])) {
    return;
  }
  originalError.call(console, ...args);
};

// Custom matchers
expect.extend({
  toHaveBeenCalledAfter(received: jest.Mock, other: jest.Mock) {
    const receivedCalls = received.mock.invocationCallOrder;
    const otherCalls = other.mock.invocationCallOrder;

    if (receivedCalls.length === 0) {
      return {
        message: () => `expected mock to be called after other mock, but it was never called`,
        pass: false,
      };
    }

    if (otherCalls.length === 0) {
      return {
        message: () => `expected mock to be called after other mock, but other mock was never called`,
        pass: false,
      };
    }

    const pass = Math.min(...receivedCalls) > Math.max(...otherCalls);

    return {
      message: () => `expected mock to${pass ? ' not' : ''} be called after other mock`,
      pass,
    };
  },
});

// Add custom types
declare global {
  // eslint-disable-next-line @typescript-eslint/no-namespace
  namespace jest {
    interface Matchers<R> {
      toHaveBeenCalledAfter(mock: jest.Mock): R;
    }
  }

  function sleep(ms: number): Promise<void>;
}
