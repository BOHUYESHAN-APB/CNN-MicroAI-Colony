#!/bin/bash

echo "================================="
echo "菌落分析前端测试"
echo "================================="

# 检查是否存在 node_modules
if [ ! -d "node_modules" ]; then
    echo "正在安装依赖..."
    npm install
fi

# 运行 TypeScript 类型检查
echo "\n🔍 正在进行类型检查..."
npm run typecheck

if [ $? -ne 0 ]; then
    echo "❌ 类型检查失败！"
    exit 1
fi

# 运行 Jest 测试
echo "\n🧪 正在运行测试..."
npm test -- --coverage --verbose

if [ $? -eq 0 ]; then
    echo "\n✅ 所有测试通过！"
    
    # 打开覆盖率报告
    echo "\n📊 测试覆盖率报告位于："
    echo "coverage/lcov-report/index.html"
    
    # 在 Linux/macOS 中尝试打开覆盖率报告
    if [[ "$OSTYPE" == "darwin"* ]]; then
        open coverage/lcov-report/index.html
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        xdg-open coverage/lcov-report/index.html
    fi
else
    echo "\n❌ 测试失败！"
    exit 1
fi

echo "\n💡 提示："
echo "- 运行 'npm test -- --watch' 进行开发测试"
echo "- 运行 'npm test -- -u' 更新快照"
echo "- 运行 'npm test -- <pattern>' 运行特定测试"
echo ""
echo "测试内容包括："
echo "- 状态管理初始化"
echo "- 相机设置更新"
echo "- 分析设置更新"
echo "- UI 设置和语言切换"
echo "- 设置持久化"
echo "- 重置功能"
