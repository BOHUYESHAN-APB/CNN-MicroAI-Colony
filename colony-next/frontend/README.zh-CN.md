# 菌落分析系统前端

[![English](https://img.shields.io/badge/lang-English-blue.svg)](./README.md) [![简体中文](https://img.shields.io/badge/语言-简体中文-red.svg)](./README.zh-CN.md)

> **⚠️ 注意:** 当前 Web UI 由于环境配置问题暂时无法运行。此问题正在调查中。
本项目是菌落分析系统的前端应用，使用 React、TypeScript 和 Tauri 构建。

## 开发

### 环境要求
- Node.js 16+
- npm 7+
- Rust (用于 Tauri)

### 设置
```bash
# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 生产环境构建
npm run build

# 预览生产构建
npm run preview
```

## 测试

### 运行测试
项目支持双语测试（中文和英文）：

```bash
# 运行所有语言的测试
npm run test:all

# 运行中文测试
npm run test:cn

# 运行英文测试
npm run test:en

# 运行特定测试套件
npm run test:ui       # UI 组件测试
npm run test:store    # 状态管理测试
npm run test:i18n     # 国际化测试

# 以监视模式运行测试
npm run test:watch
```

### 测试覆盖率
自动生成覆盖率报告：
```bash
npm run test:coverage
```
在 `coverage/lcov-report/index.html` 查看报告

### 调试测试
1. VSCode 调试器：
   - 打开测试文件
   - 设置断点
   - 按 F5 或使用运行和调试面板

2. Node 检查器：
```bash
npm run test:debug
```

## 项目结构

```
src/
├── assets/         # 静态资源
├── components/     # UI 组件
├── i18n/          # 国际化
│   ├── locales/   # 翻译文件
│   └── test-utils.ts  # 测试工具
├── layouts/       # 页面布局
├── pages/         # 页面组件
├── services/      # API 服务
├── stores/        # 状态管理
│   ├── types.ts
│   └── useAppStore.ts
├── styles/        # 全局样式
├── types/         # 类型定义
└── utils/         # 工具函数
```

## 国际化

支持的语言：
- 简体中文 (zh-CN)
- English (en-US)

### 添加翻译
1. 在语言文件中添加键值：
   - `src/i18n/locales/zh-CN.json`
   - `src/i18n/locales/en-US.json`

2. 在组件中使用翻译：
```typescript
import { useTranslation } from 'react-i18next';

function MyComponent() {
  const { t } = useTranslation();
  return <div>{t('my.translation.key')}</div>;
}
```

### 测试翻译
1. 运行国际化测试：
```bash
npm run test:i18n
```

2. 使用测试工具：
```typescript
import { translate, changeLanguage } from '../i18n/test-utils';

describe('i18n', () => {
  it('应正确翻译', () => {
    expect(translate('key', 'zh-CN')).toBe('中文');
    expect(translate('key', 'en-US')).toBe('English');
  });
});
```

## 配置文件

- `package.json` - 依赖和脚本
- `tsconfig.json` - TypeScript 配置
- `jest.config.js` - 测试配置
- `vite.config.ts` - 构建配置
- `tauri.conf.json` - Tauri 配置

## 文档
- 📖 [用户指南 (简体中文)](../docs/guides/USER_GUIDE_CN.md)
- 📖 [User Guide (English)](../docs/guides/USER_GUIDE_EN.md)
- 📖 [开发指南](../docs/development/PROJECT_STRUCTURE.md)
