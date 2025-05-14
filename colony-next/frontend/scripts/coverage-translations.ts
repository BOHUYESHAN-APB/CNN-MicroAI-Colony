export const translations = {
  'en-US': {
    title: 'Colony Analysis Test Coverage Report',
    totalCoverageLabel: 'Total Coverage',
    testCountLabel: 'Total Tests',
    timeLabel: 'Duration',
    componentLabel: 'Component',
    statementsLabel: 'Statements',
    branchesLabel: 'Branches',
    functionsLabel: 'Functions',
    linesLabel: 'Lines',
    errorsLabel: 'Test Failures',
    summaryTitle: 'Summary',
    unitTestsTitle: 'Unit Tests',
    coverageThresholds: {
      low: 'Coverage below threshold (< 80%)',
      medium: 'Coverage needs improvement (80-90%)',
      high: 'Good coverage (> 90%)'
    },
    status: {
      passed: 'Passed',
      failed: 'Failed',
      skipped: 'Skipped'
    }
  },
  'zh-CN': {
    title: '菌落分析系统测试覆盖率报告',
    totalCoverageLabel: '总覆盖率',
    testCountLabel: '测试总数',
    timeLabel: '执行时间',
    componentLabel: '组件',
    statementsLabel: '语句覆盖',
    branchesLabel: '分支覆盖',
    functionsLabel: '函数覆盖',
    linesLabel: '行覆盖',
    errorsLabel: '测试失败',
    summaryTitle: '概要',
    unitTestsTitle: '单元测试',
    coverageThresholds: {
      low: '覆盖率低于阈值 (< 80%)',
      medium: '覆盖率需要改进 (80-90%)',
      high: '覆盖率良好 (> 90%)'
    },
    status: {
      passed: '通过',
      failed: '失败',
      skipped: '跳过'
    }
  }
};

export const getCoverageClass = (percentage: number): string => {
  if (percentage < 80) return 'coverage-low';
  if (percentage < 90) return 'coverage-medium';
  return 'coverage-high';
};

export const formatDuration = (ms: number): string => {
  const seconds = Math.floor(ms / 1000);
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
};

export const formatPercentage = (value: number): string => {
  return value.toFixed(2);
};

export type CoverageData = {
  statements: number;
  branches: number;
  functions: number;
  lines: number;
};

export type ComponentCoverage = {
  name: string;
  coverage: CoverageData;
};

export type TestResult = {
  passed: boolean;
  totalTests: number;
  duration: number;
  coverage: CoverageData;
  components: ComponentCoverage[];
  errors?: string[];
};
