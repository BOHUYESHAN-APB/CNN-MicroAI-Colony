// @ts-nocheck - Disable type checking for MSW compatibility
import { setupWorker } from 'msw';
import { handlers } from './handlers';

// Create and export the worker instance
export const worker = setupWorker(...handlers);
