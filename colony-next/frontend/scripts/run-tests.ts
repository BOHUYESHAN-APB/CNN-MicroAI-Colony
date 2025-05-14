#!/usr/bin/env node
import { spawnSync } from 'child_process';
import { writeFileSync } from 'fs';
import chalk from 'chalk';
import CoverageReportGenerator from './generate-coverage';

interface TestRunResult {
  success: boolean;
  totalTests: number;
  duration: number;
  errors: string[];
}

class TestRunner {
  private startTime: number = 0;
  private generator: CoverageReportGenerator;

  constructor() {
    this.generator = new CoverageReportGenerator();
  }

  private runJest(lang: 'en-US' | 'zh-CN'): TestRunResult {
    console.log(chalk.blue(`\n🌏 Running tests in ${lang === 'zh-CN' ? 'Chinese' : 'English'}`));
    
    const env = {
      ...process.env,
      LANG: lang,
      NODE_ENV: 'test'
    };

    this.startTime = Date.now();
    const result = spawnSync('jest', ['--coverage', '--json', '--outputFile=test-results.json'], {
      stdio: 'inherit',
      env
    });

    const duration = Date.now() - this.startTime;
    
    if (result.status !== 0) {
      return {
        success: false,
        totalTests: 0,
        duration,
        errors: [`Jest process exited with code ${result.status}`]
      };
    }

    try {
      const testResults = JSON.parse(result.stdout?.toString() || '{}');
      return {
        success: testResults.success,
        totalTests: testResults.numTotalTests,
        duration,
        errors: testResults.testResults
          .filter((r: any) => r.status === 'failed')
          .map((r: any) => r.message)
      };
    } catch (error) {
      return {
        success: false,
        totalTests: 0,
        duration,
        errors: ['Failed to parse test results']
      };
    }
  }

  private generateReports(results: Record<'en-US' | 'zh-CN', TestRunResult>) {
    console.log(chalk.blue('\n📊 Generating coverage reports...'));

    Object.entries(results).forEach(([lang, result]) => {
      this.generator.generateReport(
        {
          passed: result.success,
          totalTests: result.totalTests,
          duration: result.duration,
          coverage: require('../coverage/coverage-summary.json').total,
          components: [],
          errors: result.errors
        },
        `coverage/coverage-${lang}.html`,
        lang as 'en-US' | 'zh-CN'
      );
    });
  }

  private printSummary(results: Record<'en-US' | 'zh-CN', TestRunResult>) {
    console.log(chalk.blue('\n📝 Test Summary:'));
    console.log('=====================================');

    Object.entries(results).forEach(([lang, result]) => {
      const icon = result.success ? chalk.green('✓') : chalk.red('✗');
      console.log(`\n${icon} ${lang}:`);
      console.log(`  Tests: ${result.totalTests}`);
      console.log(`  Duration: ${(result.duration / 1000).toFixed(2)}s`);
      if (result.errors.length > 0) {
        console.log(chalk.red('\n  Errors:'));
        result.errors.forEach(error => console.log(`    - ${error}`));
      }
    });
  }

  async run() {
    console.log(chalk.blue('\n🔬 Colony Analysis Test Runner'));
    console.log('=====================================');

    const results = {
      'en-US': this.runJest('en-US'),
      'zh-CN': this.runJest('zh-CN')
    };

    this.generateReports(results);
    this.printSummary(results);

    const allPassed = Object.values(results).every(r => r.success);
    if (!allPassed) {
      process.exit(1);
    }
  }
}

// Run if called directly
if (require.main === module) {
  const runner = new TestRunner();
  runner.run().catch(error => {
    console.error(chalk.red('Test runner failed:'), error);
    process.exit(1);
  });
}

export default TestRunner;
