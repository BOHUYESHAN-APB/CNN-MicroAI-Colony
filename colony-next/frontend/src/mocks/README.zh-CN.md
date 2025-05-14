# Mock Service Worker 配置

本目录包含应用程序的 Mock Service Worker (MSW) 配置。

## 文件结构

- `handlers.ts` - API 模拟处理器和响应类型
- `browser.ts` - 浏览器端 MSW 配置
- `server.ts` - Node 端 MSW 配置（用于测试）

## 类型安全说明

我们经过深思熟虑，决定在 MSW 配置文件中使用 `@ts-nocheck`，这是由于 MSW 的类型系统与 Response/MockedResponse 类型之间存在已知问题。这种方法：

1. 保持运行时功能的正常工作
2. 保留 API 响应和数据结构的类型安全
3. 避免复杂的类型断言和变通方案
4. 保持代码清晰和可维护

虽然禁用 TypeScript 检查并非理想选择，但目前这是最务实的解决方案，因为：

- 我们的 API 响应类型仍然保持完全类型安全
- MSW 配置代码量小且相对独立
- 实际应用代码保持完全类型安全
- 避免与 MSW 的内部类型系统发生冲突

## 类型安全的响应创建器

尽管为 MSW 处理器禁用了 TypeScript，我们仍然通过 `createResponse` 辅助函数保持 API 响应的类型安全：

```typescript
const createResponse = <T>(
  data: T,
  status = 200,
  message = 'Success'
): ApiResponse<T> => ({
  data,
  status,
  message
});
```

## 使用示例

```typescript
// 类型安全的模拟处理器示例
rest.get('/api/example', (_req, res, ctx) => {
  const response = createResponse<YourType>({
    // 你的类型安全数据
  });
  return res(ctx.json(response));
});
```

## 未来改进

当 MSW 解决其类型系统问题或我们找到更好的解决方案时，我们可以：

1. 移除 `@ts-nocheck` 指令
2. 添加完整的类型定义
3. 启用严格类型检查

目前，这种方法在功能性、类型安全性和可维护性之间取得了最佳平衡。
