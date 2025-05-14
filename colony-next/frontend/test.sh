#!/bin/bash

echo "================================="
echo "Colony Analysis Frontend Tests"
echo "================================="

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

# Run TypeScript type checking
echo "\n🔍 Running type checks..."
npm run typecheck

if [ $? -ne 0 ]; then
    echo "❌ Type checking failed!"
    exit 1
fi

# Run Jest tests
echo "\n🧪 Running tests..."
npm test -- --coverage --verbose

if [ $? -eq 0 ]; then
    echo "\n✅ All tests passed!"
    
    # Open coverage report
    echo "\n📊 Coverage report available at:"
    echo "coverage/lcov-report/index.html"
    
    # In Linux/macOS, try to open the coverage report
    if [[ "$OSTYPE" == "darwin"* ]]; then
        open coverage/lcov-report/index.html
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        xdg-open coverage/lcov-report/index.html
    fi
else
    echo "\n❌ Tests failed!"
    exit 1
fi

echo "\n💡 Tips:"
echo "- Run 'npm test -- --watch' for development"
echo "- Run 'npm test -- -u' to update snapshots"
echo "- Run 'npm test -- <pattern>' to run specific tests"
