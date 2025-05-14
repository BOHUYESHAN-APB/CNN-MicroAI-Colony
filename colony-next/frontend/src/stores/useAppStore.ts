import { create, StateCreator, StoreApi } from 'zustand';
import { persist } from 'zustand/middleware';
import i18n from '../i18n';

interface CameraSettings {
  resolution: string;
  fps: number;
  exposure: number;
  zoom: number;
}

interface AnalysisSettings {
  confidenceThreshold: number;
  minColonySize: number;
  maxColonySize: number;
}

type Language = 'zh-CN' | 'en-US';

interface UiSettings {
  darkMode: boolean;
  language: Language;
  showGrid: boolean;
  showLabel: boolean;
}

export interface AppState {
  camera: CameraSettings;
  analysis: AnalysisSettings;
  ui: UiSettings;
  setCameraSettings: (settings: Partial<CameraSettings>) => void;
  setAnalysisSettings: (settings: Partial<AnalysisSettings>) => void;
  setUiSettings: (settings: Partial<UiSettings>) => void;
  setLanguage: (language: Language) => void;
  resetSettings: () => void;
}

type AppStore = ReturnType<typeof createStore>;

const initialState = {
  camera: {
    resolution: '1920x1080',
    fps: 30,
    exposure: 0,
    zoom: 1.0
  },
  analysis: {
    confidenceThreshold: 0.7,
    minColonySize: 10,
    maxColonySize: 100
  },
  ui: {
    darkMode: false,
    language: 'zh-CN' as Language,
    showGrid: true,
    showLabel: true
  }
};

const createStore = (store: StateCreator<AppState>) => {
  let storeInstance: StoreApi<AppState>;

  const useStore = create<AppState>(
    persist(
      (...a) => {
        const state = store(...a);
        storeInstance = { ...a[2], getState: () => state };
        return state;
      },
      {
        name: 'app-settings',
        partialize: (state) => ({
          camera: state.camera,
          analysis: state.analysis,
          ui: state.ui
        })
      }
    )
  );

  return Object.assign(useStore, { getState: () => storeInstance.getState() });
};

export const useAppStore = createStore((set) => ({
  ...initialState,
  setCameraSettings: (settings) =>
    set((state) => ({ camera: { ...state.camera, ...settings } })),
  setAnalysisSettings: (settings) =>
    set((state) => ({ analysis: { ...state.analysis, ...settings } })),
  setUiSettings: (settings) =>
    set((state) => {
      const newSettings = { ...state.ui, ...settings };
      if (settings.language) {
        i18n.changeLanguage(settings.language);
      }
      return { ui: newSettings };
    }),
  setLanguage: (language) =>
    set((state) => {
      i18n.changeLanguage(language);
      return { ui: { ...state.ui, language } };
    }),
  resetSettings: () => set(initialState)
}));

// 导出选择器函数
export const selectCameraSettings = (state: AppState) => state.camera;
export const selectAnalysisSettings = (state: AppState) => state.analysis;
export const selectUiSettings = (state: AppState) => state.ui;
export const selectLanguage = (state: AppState) => state.ui.language;
