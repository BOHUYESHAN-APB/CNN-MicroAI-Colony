# Colony Analysis Frontend Tests

This document explains how to run and manage tests for the Colony Analysis Frontend project.

## 快速开始 / Quick Start

运行中文测试 / Run tests in Chinese:
```bash
npm run test:cn
```

Run tests in English:
```bash
npm run test:en
```

## 可用的测试命令 / Available Test Commands

```bash
# 运行所有测试 / Run all tests
npm test

# 监视模式 / Watch mode
npm run test:watch

# 覆盖率报告 / Coverage report
npm run test:coverage

# 调试模式 / Debug mode
npm run test:debug

# UI 组件测试 / UI component tests
npm run test:ui

# 状态管理测试 / Store tests
npm run test:store
```

## 测试内容 / Test Coverage

### 状态管理 / State Management
- 初始化 / Initialization
- 相机设置 / Camera Settings
- 分析设置 / Analysis Settings
- UI 设置 / UI Settings
- 国际化 / Internationalization
- 设置持久化 / Settings Persistence
- 重置功能 / Reset Functionality

### 性能要求 / Performance Requirements
- 代码覆盖率 / Code Coverage: > 80%
- 类型检查 / Type Checking: 严格模式 / Strict Mode
- 测试执行时间 / Test Execution Time: < 60s

## 调试指南 / Debugging Guide

### Visual Studio Code

1. 打开调试视图 / Open Debug View
2. 选择 "Jest Tests" / Select "Jest Tests"
3. 设置断点 / Set breakpoints
4. 按 F5 开始调试 / Press F5 to start debugging

### 浏览器调试 / Browser Debugging

```bash
npm run test:debug
```

然后在 Chrome DevTools 中打开：
Then open in Chrome DevTools:
`chrome://inspect`

## 编写测试 / Writing Tests

### 命名约定 / Naming Conventions

- `*.test.ts` - 单元测试 / Unit tests
- `*.spec.ts` - 集成测试 / Integration tests
- `__tests__/*.ts` - 测试目录 / Test directory

### 示例 / Example

```typescript
import { renderHook } from '@testing-library/react-hooks';
import { describe, it, expect } from '@jest/globals';

describe('Component/Feature', () => {
  it('should work as expected', () => {
    // Arrange
    const { result } = renderHook(() => useFeature());

    // Act
    result.current.doSomething();

    // Assert
    expect(result.current.value).toBe(expected);
  });
});
```

## 持续集成 / CI Integration

测试会在以下情况自动运行：
Tests are automatically run on:

- Pull Requests
- Push to `main`
- Daily Scheduled Runs

## 故障排除 / Troubleshooting

### 常见问题 / Common Issues

1. 类型错误 / Type Errors
```bash
npm run typecheck
```

2. 测试失败 / Test Failures
```bash
npm test -- --verbose
```

3. 快照更新 / Snapshot Updates
```bash
npm test -- -u
```

### 获取帮助 / Getting Help

如有问题，请：
If you need help:

1. 检查测试日志 / Check test logs
2. 运行详细模式 / Run in verbose mode
3. 查看覆盖率报告 / Review coverage report
4. 提交 issue / Submit an issue
