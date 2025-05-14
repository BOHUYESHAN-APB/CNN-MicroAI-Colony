#!/usr/bin/env node
import { spawnSync } from 'child_process';
import chalk from 'chalk';
import TestReportGenerator from './generate-test-report';
import { TestReport } from './test-docs-translations';

type SupportedLanguage = 'en-US' | 'zh-CN';

class TestExecutor {
  private startTime: number = Date.now();
  private generator: TestReportGenerator;

  constructor() {
    this.generator = new TestReportGenerator();
  }

  private runTests(lang: SupportedLanguage): boolean {
    console.log(chalk.blue(`\n🌏 Running tests in ${lang === 'zh-CN' ? 'Chinese' : 'English'}`));
    
    const result = spawnSync('jest', ['--coverage', '--json', '--outputFile=test-results.json'], {
      stdio: 'inherit',
      env: { ...process.env, LANG: lang }
    });

    return result.status === 0;
  }

  private generateTestReport(success: boolean, lang: SupportedLanguage) {
    try {
      const testResults = require('../test-results.json');
      const coverageResults = require('../coverage/coverage-summary.json');

      const report: TestReport = {
        title: lang === 'zh-CN' ? '菌落分析测试报告' : 'Colony Analysis Test Report',
        summary: success ? 
          (lang === 'zh-CN' ? '所有测试通过' : 'All tests passed') :
          (lang === 'zh-CN' ? '测试执行出现错误' : 'Test execution encountered errors'),
        testSuites: testResults.testResults.map((suite: any) => ({
          name: suite.name,
          status: suite.status,
          coverage: coverageResults[suite.name]?.statements?.pct || 0,
          duration: suite.duration,
          failures: suite.failureMessages,
          testCases: suite.testResults.map((test: any) => ({
            name: test.title,
            result: test.status,
            duration: test.duration
          }))
        })),
        components: Object.entries(coverageResults)
          .filter(([name]) => name !== 'total')
          .map(([name, data]: [string, any]) => ({
            name,
            statements: data.statements.pct,
            branches: data.branches.pct,
            functions: data.functions.pct,
            lines: data.lines.pct
          })),
        totalTime: Date.now() - this.startTime,
        avgTime: testResults.testResults.reduce((acc: number, suite: any) => 
          acc + suite.duration, 0) / testResults.testResults.length,
        maxTime: Math.max(...testResults.testResults.map((suite: any) => suite.duration)),
        minTime: Math.min(...testResults.testResults.map((suite: any) => suite.duration)),
        environment: {
          nodeVersion: process.version,
          osInfo: process.platform,
          jestVersion: require('../package.json').devDependencies.jest,
          tsVersion: require('../package.json').devDependencies.typescript,
          reactVersion: require('../package.json').dependencies.react,
          language: lang,
          timezone: Intl.DateTimeFormat().resolvedOptions().timeZone
        },
        timestamp: new Date().toLocaleString(lang)
      };

      this.generator.generateReport(report, lang, `test-report-${lang}.md`);
      console.log(chalk.green(`\n📝 Test report generated: test-report-${lang}.md`));
    } catch (error) {
      console.error(chalk.red('\n❌ Failed to generate test report:'), error);
    }
  }

  async run(languages: SupportedLanguage[] = ['en-US', 'zh-CN']) {
    console.log(chalk.blue('\n🔬 Colony Analysis Test Runner'));
    console.log('=====================================');

    let allPassed = true;
    
    for (const lang of languages) {
      const success = this.runTests(lang);
      this.generateTestReport(success, lang);
      allPassed = allPassed && success;
    }

    if (!allPassed) {
      console.error(chalk.red('\n❌ Some tests failed'));
      process.exit(1);
    }

    console.log(chalk.green('\n✅ All tests passed'));
  }

  static detectLanguage(): SupportedLanguage[] {
    const envLang = process.env.LANG?.toLowerCase() || '';
    if (envLang.startsWith('zh')) return ['zh-CN'];
    if (envLang.startsWith('en')) return ['en-US'];
    return ['en-US', 'zh-CN'];
  }
}

// Run if called directly
if (require.main === module) {
  const executor = new TestExecutor();
  executor.run(TestExecutor.detectLanguage()).catch(error => {
    console.error(chalk.red('Test execution failed:'), error);
    process.exit(1);
  });
}

export default TestExecutor;
