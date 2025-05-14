// @ts-nocheck - Disable type checking for MSW compatibility
import { rest } from 'msw';

// Common response types
interface ApiResponse<T> {
  data: T;
  status: number;
  message: string;
}

// API endpoints and their response types
interface CameraSettings {
  resolution: string;
  fps: number;
  exposure: number;
  gain: number;
}

interface AnalysisResult {
  id: string;
  timestamp: string;
  colonyCount: number;
  image: string;
  metadata: Record<string, unknown>;
}

// Type-safe response creator
const createResponse = <T>(
  data: T,
  status = 200,
  message = 'Success'
): ApiResponse<T> => ({
  data,
  status,
  message
});

// Request handlers
export const handlers = [
  // Camera settings
  rest.get('/api/camera/settings', (_req, res, ctx) => {
    const response = createResponse<CameraSettings>({
      resolution: '1920x1080',
      fps: 30,
      exposure: 100,
      gain: 1.0
    });
    return res(ctx.json(response));
  }),

  // Analysis results
  rest.get('/api/analysis/history', (_req, res, ctx) => {
    const response = createResponse<AnalysisResult[]>([{
      id: '1',
      timestamp: new Date().toISOString(),
      colonyCount: 123,
      image: 'base64-encoded-image',
      metadata: {
        temperature: 25,
        humidity: 60
      }
    }]);
    return res(ctx.json(response));
  }),

  // Error handling example
  rest.post('/api/analysis/start', (_req, res, ctx) => {
    const response = createResponse<null>(null, 400, 'Camera not connected');
    return res(ctx.status(400), ctx.json(response));
  }),

  // Websocket status
  rest.get('/api/ws/status', (_req, res, ctx) => {
    const response = createResponse<{connected: boolean; lastPing: string}>({
      connected: true,
      lastPing: new Date().toISOString()
    });
    return res(ctx.json(response));
  }),

  // i18n test endpoint
  rest.get('/api/i18n/test', (req, res, ctx) => {
    const lang = req.headers.get('Accept-Language') || 'en-US';
    const response = createResponse<{greeting: string; language: string}>({
      greeting: lang.startsWith('zh') ? '你好' : 'Hello',
      language: lang
    });
    return res(ctx.json(response));
  })
];

// Export types and helpers
export type { ApiResponse, CameraSettings, AnalysisResult };
export { createResponse };
