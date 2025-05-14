declare module 'zustand' {
  export interface StoreApi<T> {
    setState: (
      partial: T | Partial<T> | ((state: T) => T | Partial<T>),
      replace?: boolean
    ) => void;
    getState: () => T;
    subscribe: (listener: (state: T, prevState: T) => void) => () => void;
    destroy: () => void;
  }

  export type StateCreator<T, U = T> = (
    set: StoreApi<T>['setState'],
    get: StoreApi<T>['getState'],
    api: StoreApi<T>
  ) => U;

  export function create<T>(stateCreator: StateCreator<T>): () => T;
}

declare module 'zustand/middleware' {
  import { StateCreator, StoreApi } from 'zustand';

  export interface PersistOptions<T> {
    name: string;
    getStorage?: () => Storage;
    partialize?: (state: T) => Partial<T>;
    version?: number;
    migrate?: (persistedState: any, version: number) => T | Promise<T>;
    merge?: (persistedState: any, currentState: T) => T;
    onRehydrateStorage?: (state: T) => ((state?: T, error?: Error) => void) | void;
  }

  export function persist<T>(
    config: StateCreator<T>,
    options: PersistOptions<T>
  ): StateCreator<T>;
}
