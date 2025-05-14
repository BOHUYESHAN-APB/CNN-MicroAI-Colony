import '@testing-library/jest-dom';

declare global {
  namespace jest {
    interface Matchers<R> {
      toBeInTheDocument(): R;
      toHaveStyle(style: Record<string, any>): R;
    }
  }

  interface Window {
    matchMedia: (query: string) => Partial<MediaQueryList>;
  }
}

type JestMockFn = {
  (): boolean;
  mockImplementation: (fn: () => any) => JestMockFn;
  mockReturnValue: (value: any) => JestMockFn;
  mockClear: () => JestMockFn;
};

type MediaQueryListMock = {
  matches: boolean;
  media: string;
  onchange: null;
  addListener: JestMockFn;
  removeListener: JestMockFn;
  addEventListener: JestMockFn;
  removeEventListener: JestMockFn;
  dispatchEvent: JestMockFn;
};

export type { JestMockFn, MediaQueryListMock };

// This empty export makes it a module
export {};
