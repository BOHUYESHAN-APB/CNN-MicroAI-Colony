# {{TITLE}}

{{SUMMARY}}

## {{TEST_STATUS}}

{{#each testSuites}}
### {{name}}
- {{STATUS_LABEL}}: {{status}}
- {{COVERAGE_LABEL}}: {{coverage}}%
- {{DURATION_LABEL}}: {{duration}}ms
{{#if failures}}
#### {{FAILURES_LABEL}}:
{{#each failures}}
- {{this}}
{{/each}}
{{/if}}

#### {{TEST_CASES_LABEL}}:
{{#each testCases}}
- {{this.name}}: {{this.result}}
{{/each}}

{{/each}}

## {{COVERAGE_SECTION}}

| {{COMPONENT_LABEL}} | {{STATEMENTS_LABEL}} | {{BRANCHES_LABEL}} | {{FUNCTIONS_LABEL}} | {{LINES_LABEL}} |
|-------------------|-----------------|--------------|---------------|------------|
{{#each components}}
| {{name}} | {{statements}}% | {{branches}}% | {{functions}}% | {{lines}}% |
{{/each}}

## {{PERFORMANCE_SECTION}}

- {{TOTAL_TIME_LABEL}}: {{totalTime}}ms
- {{AVG_TIME_LABEL}}: {{avgTime}}ms
- {{MAX_TIME_LABEL}}: {{maxTime}}ms
- {{MIN_TIME_LABEL}}: {{minTime}}ms

{{#if warnings}}
## {{WARNINGS_SECTION}}
{{#each warnings}}
- {{this}}
{{/each}}
{{/if}}

## {{ENVIRONMENT_SECTION}}

- Node: {{nodeVersion}}
- OS: {{osInfo}}
- Jest: {{jestVersion}}
- TypeScript: {{tsVersion}}
- React: {{reactVersion}}
- {{LANGUAGE_LABEL}}: {{language}}
- {{TIMEZONE_LABEL}}: {{timezone}}

{{#if recommendations}}
## {{RECOMMENDATIONS_SECTION}}
{{#each recommendations}}
- {{this}}
{{/each}}
{{/if}}

---
_{{GENERATED_AT}}: {{timestamp}}_
