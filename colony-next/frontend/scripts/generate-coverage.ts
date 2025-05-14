import { readFileSync, writeFileSync } from 'fs';
import { join } from 'path';
import { translations, getCoverageClass, formatDuration, formatPercentage, TestResult } from './coverage-translations';

class CoverageReportGenerator {
  private template: string;
  
  constructor() {
    this.template = readFileSync(
      join(__dirname, 'coverage-template.html'),
      'utf-8'
    );
  }

  private replaceTemplateVariables(content: string, data: TestResult, lang: 'en-US' | 'zh-CN'): string {
    const t = translations[lang];
    const avgCoverage = (
      data.coverage.statements +
      data.coverage.branches +
      data.coverage.functions +
      data.coverage.lines
    ) / 4;

    let result = content
      .replace('{{TITLE}}', t.title)
      .replace('{{TOTAL_COVERAGE_LABEL}}', t.totalCoverageLabel)
      .replace('{{TEST_COUNT_LABEL}}', t.testCountLabel)
      .replace('{{TIME_LABEL}}', t.timeLabel)
      .replace('{{COMPONENT_LABEL}}', t.componentLabel)
      .replace('{{STATEMENTS_LABEL}}', t.statementsLabel)
      .replace('{{BRANCHES_LABEL}}', t.branchesLabel)
      .replace('{{FUNCTIONS_LABEL}}', t.functionsLabel)
      .replace('{{LINES_LABEL}}', t.linesLabel)
      .replace('{{TOTAL_COVERAGE}}', formatPercentage(avgCoverage))
      .replace('{{TOTAL_COVERAGE_CLASS}}', getCoverageClass(avgCoverage))
      .replace('{{TOTAL_TESTS}}', data.totalTests.toString())
      .replace('{{TOTAL_TIME}}', formatDuration(data.duration))
      .replace('{{EN_ACTIVE}}', lang === 'en-US' ? 'class="active"' : '')
      .replace('{{ZH_ACTIVE}}', lang === 'zh-CN' ? 'class="active"' : '');

    // Generate table rows
    const tableRows = data.components.map(component => `
      <tr>
        <td>${component.name}</td>
        <td>
          <div class="coverage-bar">
            <div class="coverage-filled ${getCoverageClass(component.coverage.statements)}"
                 style="width: ${component.coverage.statements}%"></div>
          </div>
          ${formatPercentage(component.coverage.statements)}%
        </td>
        <td>
          <div class="coverage-bar">
            <div class="coverage-filled ${getCoverageClass(component.coverage.branches)}"
                 style="width: ${component.coverage.branches}%"></div>
          </div>
          ${formatPercentage(component.coverage.branches)}%
        </td>
        <td>
          <div class="coverage-bar">
            <div class="coverage-filled ${getCoverageClass(component.coverage.functions)}"
                 style="width: ${component.coverage.functions}%"></div>
          </div>
          ${formatPercentage(component.coverage.functions)}%
        </td>
        <td>
          <div class="coverage-bar">
            <div class="coverage-filled ${getCoverageClass(component.coverage.lines)}"
                 style="width: ${component.coverage.lines}%"></div>
          </div>
          ${formatPercentage(component.coverage.lines)}%
        </td>
      </tr>
    `).join('');

    result = result.replace('{{TABLE_ROWS}}', tableRows);

    // Handle errors section
    if (data.errors && data.errors.length > 0) {
      const errorItems = data.errors.map(error => `<li>${error}</li>`).join('');
      result = result
        .replace('{{#if ERRORS}}', '')
        .replace('{{/if}}', '')
        .replace('{{ERRORS_LABEL}}', t.errorsLabel)
        .replace('{{ERROR_ITEMS}}', errorItems);
    } else {
      result = result.replace(/{{#if ERRORS}}[\s\S]*?{{\/if}}/g, '');
    }

    return result;
  }

  generateReport(data: TestResult, outputPath: string, lang: 'en-US' | 'zh-CN'): void {
    const report = this.replaceTemplateVariables(this.template, data, lang);
    writeFileSync(outputPath, report);
  }
}

// Export the generator class
export default CoverageReportGenerator;

// CLI support
if (require.main === module) {
  const coverageData = JSON.parse(readFileSync('coverage/coverage-summary.json', 'utf-8'));
  const testResults = JSON.parse(readFileSync('test-results.json', 'utf-8'));
  
  const generator = new CoverageReportGenerator();
  
  // Generate English report
  generator.generateReport({
    ...testResults,
    coverage: coverageData.total,
    components: Object.entries(coverageData).filter(([key]) => key !== 'total')
      .map(([name, data]) => ({
        name,
        coverage: data as any
      }))
  }, 'coverage/coverage-en.html', 'en-US');
  
  // Generate Chinese report
  generator.generateReport({
    ...testResults,
    coverage: coverageData.total,
    components: Object.entries(coverageData).filter(([key]) => key !== 'total')
      .map(([name, data]) => ({
        name,
        coverage: data as any
      }))
  }, 'coverage/coverage-zh.html', 'zh-CN');
}
