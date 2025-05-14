# Colony Analysis Frontend

[![English](https://img.shields.io/badge/lang-English-blue.svg)](./README.md) [![简体中文](https://img.shields.io/badge/语言-简体中文-red.svg)](./README.zh-CN.md)

This is the frontend application for the Colony Analysis system, built with React, TypeScript, and Tauri.

## Development

### Prerequisites
- Node.js 16+
- npm 7+
- Rust (for Tauri)

### Setup
```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Testing

### Running Tests
The project supports bilingual testing (Chinese and English):

```bash
# Run all tests with both languages
npm run test:all

# Run tests in Chinese
npm run test:cn

# Run tests in English
npm run test:en

# Run specific test suites
npm run test:ui       # UI components
npm run test:store    # State management
npm run test:i18n     # Internationalization

# Run tests in watch mode
npm run test:watch
```

### Test Coverage
Coverage report is automatically generated:
```bash
npm run test:coverage
```
View the report at `coverage/lcov-report/index.html`

### Debugging Tests
1. VSCode Debugger:
   - Open test file
   - Set breakpoints
   - Press F5 or use Run & Debug panel

2. Node Inspector:
```bash
npm run test:debug
```

## Project Structure

```
src/
├── assets/         # Static assets
├── components/     # UI components
├── i18n/          # Internationalization
│   ├── locales/   # Translation files
│   └── test-utils.ts  # Testing utilities
├── layouts/       # Page layouts
├── pages/         # Page components
├── services/      # API services
├── stores/        # State management
│   ├── types.ts
│   └── useAppStore.ts
├── styles/        # Global styles
├── types/         # Type definitions
└── utils/         # Utility functions
```

## Internationalization

Supported languages:
- 简体中文 (zh-CN)
- English (en-US)

### Adding Translations
1. Add keys to locale files:
   - `src/i18n/locales/zh-CN.json`
   - `src/i18n/locales/en-US.json`

2. Use translations in components:
```typescript
import { useTranslation } from 'react-i18next';

function MyComponent() {
  const { t } = useTranslation();
  return <div>{t('my.translation.key')}</div>;
}
```

### Testing Translations
1. Run i18n tests:
```bash
npm run test:i18n
```

2. Use test utilities:
```typescript
import { translate, changeLanguage } from '../i18n/test-utils';

describe('i18n', () => {
  it('should translate correctly', () => {
    expect(translate('key', 'zh-CN')).toBe('中文');
    expect(translate('key', 'en-US')).toBe('English');
  });
});
```

## Configuration Files

- `package.json` - Dependencies and scripts
- `tsconfig.json` - TypeScript configuration
- `jest.config.js` - Test configuration
- `vite.config.ts` - Build configuration
- `tauri.conf.json` - Tauri configuration

## Documentation
- 📖 [User Guide (English)](../docs/guides/USER_GUIDE_EN.md)
- 📖 [用户指南 (简体中文)](../docs/guides/USER_GUIDE_CN.md)
- 📖 [Development Guide](../docs/development/PROJECT_STRUCTURE.md)
