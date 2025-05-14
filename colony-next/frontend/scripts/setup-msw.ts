import { execSync } from 'child_process';
import { mkdirSync, writeFileSync } from 'fs';
import { join } from 'path';
import chalk from 'chalk';

/**
 * Sets up Mock Service Worker for the project
 */
async function setupMSW() {
  console.log(chalk.blue('\nSetting up Mock Service Worker...'));

  try {
    // Create public directory if it doesn't exist
    const publicDir = join(__dirname, '../public');
    mkdirSync(publicDir, { recursive: true });

    // Initialize MSW
    execSync('npx msw init public/ --save', {
      stdio: 'inherit',
      cwd: join(__dirname, '..')
    });

    // Create browser mock setup file
    const browserMockSetup = `
import { setupWorker } from 'msw';
import { handlers } from './handlers';

export const worker = setupWorker(...handlers);

// Conditionally start the worker
if (process.env.NODE_ENV === 'development') {
  worker.start({
    onUnhandledRequest: 'bypass' // Don't warn about unhandled requests
  }).catch(console.error);
}
    `.trim();

    writeFileSync(
      join(__dirname, '../src/mocks/browser.ts'),
      browserMockSetup
    );

    // Add MSW to package.json scripts
    const packageJson = require('../package.json');
    packageJson.scripts = {
      ...packageJson.scripts,
      'msw:init': 'msw init public/',
      'msw:update': 'npm run msw:init'
    };
    writeFileSync(
      join(__dirname, '../package.json'),
      JSON.stringify(packageJson, null, 2)
    );

    // Add MSW import to main entry point
    const mainEntryPoint = `
// MSW Development Setup
if (process.env.NODE_ENV === 'development') {
  const { worker } = await import('./mocks/browser');
  worker.start();
}
    `.trim();

    // Create entry point file if it doesn't exist
    writeFileSync(
      join(__dirname, '../src/mocks/setup.ts'),
      mainEntryPoint
    );

    console.log(chalk.green('\n✅ Mock Service Worker setup complete!'));
    console.log(chalk.gray('\nYou can now use MSW by:'));
    console.log(chalk.gray('1. Import the worker in your entry file'));
    console.log(chalk.gray('2. Add handlers in src/mocks/handlers.ts'));
    console.log(chalk.gray('3. Start the development server\n'));

  } catch (error) {
    console.error(chalk.red('\n❌ Failed to setup Mock Service Worker:'));
    console.error(error);
    process.exit(1);
  }
}

// Run setup if called directly
if (require.main === module) {
  setupMSW().catch(console.error);
}

export default setupMSW;
