import { ResponseResolver, DefaultRequestBody } from 'msw';

declare module 'msw' {
  export interface ResponseComposition<T = any> {
    (callback: ResponseTransformer): Response;
    json<U = T>(data: U): ResponseTransformer;
    text(data: string): ResponseTransformer;
    status(code: number): ResponseTransformer;
    set(headers: Record<string, string>): ResponseTransformer;
    delay(ms: number): ResponseTransformer;
  }

  export interface ResponseTransformer {
    (response: Response): Response | Promise<Response>;
  }

  export interface RestContext {
    delay: (ms: number) => ResponseTransformer;
    fetch: (input: RequestInfo, init?: RequestInit) => Promise<Response>;
    json: <T = any>(data: T) => ResponseTransformer;
    set: (headers: Record<string, string>) => ResponseTransformer;
    status: (statusCode: number) => ResponseTransformer;
    text: (body: string) => ResponseTransformer;
    data: <T = any>(data: T) => ResponseTransformer;
  }

  export interface RequestHandler<
    RequestBody = DefaultRequestBody,
    PathParams = Record<string, string>
  > extends ResponseResolver<any, any> {}

  export const rest: RestMethods;

  interface RestMethods {
    get: <T = any>(
      path: string,
      resolver: ResponseResolver<T>
    ) => RequestHandler<T>;
    post: <T = any>(
      path: string,
      resolver: ResponseResolver<T>
    ) => RequestHandler<T>;
    put: <T = any>(
      path: string,
      resolver: ResponseResolver<T>
    ) => RequestHandler<T>;
    delete: <T = any>(
      path: string,
      resolver: ResponseResolver<T>
    ) => RequestHandler<T>;
    patch: <T = any>(
      path: string,
      resolver: ResponseResolver<T>
    ) => RequestHandler<T>;
    options: <T = any>(
      path: string,
      resolver: ResponseResolver<T>
    ) => RequestHandler<T>;
  }

  export interface ResponseResolver<
    RequestBodyType = any,
    ResponseBodyType = any
  > {
    (
      req: RestRequest<RequestBodyType>,
      res: ResponseComposition<ResponseBodyType>,
      ctx: RestContext
    ): Promise<MockedResponse> | MockedResponse;
  }

  export interface MockedResponse extends Response {
    [Symbol.toStringTag]: string;
  }

  export interface RestRequest<T = any> extends Request {
    params: Record<string, string>;
    body: T;
  }

  export const setupWorker: (...handlers: RequestHandler[]) => SetupWorkerApi;

  export interface SetupWorkerApi {
    start: (options?: StartOptions) => Promise<void>;
    stop: () => void;
    use: (...handlers: RequestHandler[]) => void;
    resetHandlers: () => void;
    listHandlers: () => RequestHandler[];
  }

  export interface StartOptions {
    serviceWorker?: {
      url: string;
      options?: ServiceWorkerRegistrationOptions;
    };
    quiet?: boolean;
    onUnhandledRequest?: 'bypass' | 'warn' | 'error' | ((req: Request, print: PrintHandlerInfo) => void);
  }

  export interface PrintHandlerInfo {
    warning: () => void;
    error: () => void;
    info: () => void;
  }
}
