import { execSync } from 'child_process';
import chalk from 'chalk';

interface TestResult {
  passed: boolean;
  coverage: {
    lines: number;
    functions: number;
    statements: number;
  };
  duration: number;
}

const runTests = (lang: 'zh-CN' | 'en-US'): TestResult => {
  console.log(chalk.blue(`\n开始运行测试 / Starting tests (${lang})`));
  console.log(chalk.gray('='.repeat(50)));

  const startTime = Date.now();
  try {
    // Run tests with specified language
    const env = { ...process.env, LANG: lang };
    execSync(`jest --coverage --verbose`, { 
      env,
      stdio: 'inherit'
    });

    // Parse coverage report
    const coverage = JSON.parse(
      execSync('cat coverage/coverage-summary.json', { encoding: 'utf-8' })
    ).total;

    return {
      passed: true,
      coverage: {
        lines: coverage.lines.pct,
        functions: coverage.functions.pct,
        statements: coverage.statements.pct
      },
      duration: Date.now() - startTime
    };
  } catch (error) {
    console.error(chalk.red('\n测试失败 / Tests failed:'));
    console.error(error);
    return {
      passed: false,
      coverage: { lines: 0, functions: 0, statements: 0 },
      duration: Date.now() - startTime
    };
  }
};

const printResults = (results: { [key: string]: TestResult }) => {
  console.log(chalk.blue('\n测试结果汇总 / Test Results Summary'));
  console.log(chalk.gray('='.repeat(50)));

  Object.entries(results).forEach(([lang, result]) => {
    const icon = result.passed ? chalk.green('✓') : chalk.red('✗');
    console.log(`\n${icon} ${lang}:`);
    if (result.passed) {
      console.log(chalk.green(`  通过 / Passed (${result.duration}ms)`));
      console.log(chalk.cyan('  覆盖率 / Coverage:'));
      console.log(`    行覆盖率 / Lines: ${result.coverage.lines}%`);
      console.log(`    函数覆盖率 / Functions: ${result.coverage.functions}%`);
      console.log(`    语句覆盖率 / Statements: ${result.coverage.statements}%`);
    } else {
      console.log(chalk.red(`  失败 / Failed (${result.duration}ms)`));
    }
  });
};

const main = () => {
  console.log(chalk.blue('\n菌落分析系统测试 / Colony Analysis System Tests'));
  console.log(chalk.gray('='.repeat(50)));

  const results = {
    'zh-CN': runTests('zh-CN'),
    'en-US': runTests('en-US')
  };

  printResults(results);

  // Exit with appropriate code
  const allPassed = Object.values(results).every(r => r.passed);
  process.exit(allPassed ? 0 : 1);
};

main();
