export const testDocsTranslations = {
  'en-US': {
    title: 'Colony Analysis Test Report',
    summary: 'Test execution summary and detailed results',
    testStatus: 'Test Status',
    statusLabel: 'Status',
    coverageLabel: 'Coverage',
    durationLabel: 'Duration',
    failuresLabel: 'Failures',
    testCasesLabel: 'Test Cases',
    coverageSection: 'Code Coverage',
    componentLabel: 'Component',
    statementsLabel: 'Statements',
    branchesLabel: 'Branches',
    functionsLabel: 'Functions',
    linesLabel: 'Lines',
    performanceSection: 'Performance Metrics',
    totalTimeLabel: 'Total Execution Time',
    avgTimeLabel: 'Average Test Duration',
    maxTimeLabel: 'Longest Test',
    minTimeLabel: 'Shortest Test',
    warningsSection: 'Warnings',
    environmentSection: 'Test Environment',
    languageLabel: 'Language',
    timezoneLabel: 'Timezone',
    recommendationsSection: 'Recommendations',
    generatedAt: 'Report generated at',
    status: {
      passed: 'Passed',
      failed: 'Failed',
      skipped: 'Skipped',
      pending: 'Pending'
    },
    coverage: {
      good: 'Good coverage (≥90%)',
      acceptable: 'Acceptable coverage (≥80%)',
      poor: 'Poor coverage (<80%)'
    }
  },
  'zh-CN': {
    title: '菌落分析测试报告',
    summary: '测试执行摘要和详细结果',
    testStatus: '测试状态',
    statusLabel: '状态',
    coverageLabel: '覆盖率',
    durationLabel: '执行时间',
    failuresLabel: '失败项',
    testCasesLabel: '测试用例',
    coverageSection: '代码覆盖率',
    componentLabel: '组件',
    statementsLabel: '语句覆盖',
    branchesLabel: '分支覆盖',
    functionsLabel: '函数覆盖',
    linesLabel: '行覆盖',
    performanceSection: '性能指标',
    totalTimeLabel: '总执行时间',
    avgTimeLabel: '平均测试时间',
    maxTimeLabel: '最长测试',
    minTimeLabel: '最短测试',
    warningsSection: '警告信息',
    environmentSection: '测试环境',
    languageLabel: '语言',
    timezoneLabel: '时区',
    recommendationsSection: '建议',
    generatedAt: '报告生成于',
    status: {
      passed: '通过',
      failed: '失败',
      skipped: '跳过',
      pending: '待处理'
    },
    coverage: {
      good: '覆盖率良好 (≥90%)',
      acceptable: '覆盖率尚可 (≥80%)',
      poor: '覆盖率不足 (<80%)'
    }
  }
};

export interface TestCase {
  name: string;
  result: string;
  duration: number;
}

export interface TestSuite {
  name: string;
  status: string;
  coverage: number;
  duration: number;
  failures?: string[];
  testCases: TestCase[];
}

export interface Component {
  name: string;
  statements: number;
  branches: number;
  functions: number;
  lines: number;
}

export interface TestReport {
  title: string;
  summary: string;
  testSuites: TestSuite[];
  components: Component[];
  totalTime: number;
  avgTime: number;
  maxTime: number;
  minTime: number;
  warnings?: string[];
  recommendations?: string[];
  environment: {
    nodeVersion: string;
    osInfo: string;
    jestVersion: string;
    tsVersion: string;
    reactVersion: string;
    language: string;
    timezone: string;
  };
  timestamp: string;
}

export const formatDuration = (ms: number): string => {
  if (ms < 1000) return `${ms}ms`;
  const seconds = Math.floor(ms / 1000);
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
};

export const getCoverageStatus = (coverage: number, lang: 'en-US' | 'zh-CN'): string => {
  const t = testDocsTranslations[lang].coverage;
  if (coverage >= 90) return t.good;
  if (coverage >= 80) return t.acceptable;
  return t.poor;
};
