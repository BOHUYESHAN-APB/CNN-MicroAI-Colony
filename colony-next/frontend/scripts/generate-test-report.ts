import { readFileSync, writeFileSync } from 'fs';
import { join } from 'path';
import * as os from 'os';
import { testDocsTranslations, TestReport, formatDuration, getCoverageStatus } from './test-docs-translations';

class TestReportGenerator {
  private template: string;

  constructor() {
    this.template = readFileSync(
      join(__dirname, 'test-docs-template.md'),
      'utf-8'
    );
  }

  private getEnvironmentInfo() {
    const pkg = JSON.parse(readFileSync(join(__dirname, '../package.json'), 'utf-8'));
    return {
      nodeVersion: process.version,
      osInfo: `${os.type()} ${os.release()}`,
      jestVersion: pkg.devDependencies.jest,
      tsVersion: pkg.devDependencies.typescript,
      reactVersion: pkg.dependencies.react,
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone
    };
  }

  private replaceTemplateVariables(content: string, data: TestReport, lang: 'en-US' | 'zh-CN'): string {
    const t = testDocsTranslations[lang];
    let result = content;

    // Replace basic variables
    Object.entries(t).forEach(([key, value]) => {
      if (typeof value === 'string') {
        result = result.replace(`{{${key.toUpperCase()}}}`, value);
      }
    });

    // Replace test suites
    const suitesContent = data.testSuites.map(suite => {
      let suiteContent = `### ${suite.name}\n`;
      suiteContent += `- ${t.statusLabel}: ${t.status[suite.status as keyof typeof t.status]}\n`;
      suiteContent += `- ${t.coverageLabel}: ${suite.coverage}% (${getCoverageStatus(suite.coverage, lang)})\n`;
      suiteContent += `- ${t.durationLabel}: ${formatDuration(suite.duration)}\n`;

      if (suite.failures && suite.failures.length > 0) {
        suiteContent += `\n#### ${t.failuresLabel}:\n`;
        suiteContent += suite.failures.map(failure => `- ${failure}`).join('\n');
        suiteContent += '\n';
      }

      suiteContent += `\n#### ${t.testCasesLabel}:\n`;
      suiteContent += suite.testCases
        .map(test => `- ${test.name}: ${t.status[test.result as keyof typeof t.status]} (${formatDuration(test.duration)})`)
        .join('\n');

      return suiteContent;
    }).join('\n\n');

    result = result.replace('{{#each testSuites}}{{/each}}', suitesContent);

    // Replace components table
    const componentsContent = data.components
      .map(comp => `| ${comp.name} | ${comp.statements}% | ${comp.branches}% | ${comp.functions}% | ${comp.lines}% |`)
      .join('\n');

    result = result.replace('{{#each components}}{{/each}}', componentsContent);

    // Replace performance metrics
    result = result
      .replace('{{totalTime}}', formatDuration(data.totalTime))
      .replace('{{avgTime}}', formatDuration(data.avgTime))
      .replace('{{maxTime}}', formatDuration(data.maxTime))
      .replace('{{minTime}}', formatDuration(data.minTime));

    // Replace warnings if any
    if (data.warnings && data.warnings.length > 0) {
      const warningsContent = data.warnings.map(w => `- ${w}`).join('\n');
      result = result.replace('{{#if warnings}}{{/if}}', warningsContent);
    } else {
      result = result.replace(/{{#if warnings}}[\s\S]*?{{\/if}}/g, '');
    }

    // Replace environment info
    const env = { ...this.getEnvironmentInfo(), language: lang };
    Object.entries(env).forEach(([key, value]) => {
      result = result.replace(`{{${key}}}`, value);
    });

    // Replace recommendations if any
    if (data.recommendations && data.recommendations.length > 0) {
      const recsContent = data.recommendations.map(r => `- ${r}`).join('\n');
      result = result.replace('{{#if recommendations}}{{/if}}', recsContent);
    } else {
      result = result.replace(/{{#if recommendations}}[\s\S]*?{{\/if}}/g, '');
    }

    // Replace timestamp
    result = result.replace('{{timestamp}}', new Date().toLocaleString(lang));

    return result;
  }

  generateReport(data: TestReport, lang: 'en-US' | 'zh-CN', outputPath: string) {
    const report = this.replaceTemplateVariables(this.template, data, lang);
    writeFileSync(outputPath, report);
  }
}

// Export the generator class
export default TestReportGenerator;

// CLI support
if (require.main === module) {
  const testResults = JSON.parse(readFileSync('test-results.json', 'utf-8'));
  
  const generator = new TestReportGenerator();
  
  // Generate English report
  generator.generateReport(testResults, 'en-US', 'test-report-en.md');
  
  // Generate Chinese report
  generator.generateReport(testResults, 'zh-CN', 'test-report-zh.md');
}
