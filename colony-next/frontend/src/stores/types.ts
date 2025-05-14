export interface CameraSettings {
  resolution: string;
  fps: number;
}

export interface AnalysisSettings {
  confidenceThreshold: number;
  minColonySize: number;
}

export interface UiSettings {
  darkMode: boolean;
  language: string;
}

export interface Statistics {
  totalAnalyzed: number;
  averageCount: number;
  lastAnalysis: string | null;
}

export interface Colony {
  position: [number, number];
  size: number;
  confidence: number;
}

export interface AnalysisResults {
  count: number;
  colonies: Colony[];
  tilt: [number, number];
}

export interface AppState {
  cameraSettings: CameraSettings;
  analysisSettings: AnalysisSettings;
  uiSettings: UiSettings;
  statistics: Statistics;
  updateCameraSettings: (settings: Partial<CameraSettings>) => void;
  updateAnalysisSettings: (settings: Partial<AnalysisSettings>) => void;
  updateUiSettings: (settings: Partial<UiSettings>) => void;
  updateStatistics: (data: Partial<Statistics>) => void;
  resetSettings: () => void;
}

export interface AnalysisState {
  analyzing: boolean;
  progress: number;
  results: AnalysisResults | null;
  startAnalysis: () => void;
  updateProgress: (progress: number) => void;
  setResults: (results: AnalysisResults | null) => void;
  resetAnalysis: () => void;
}
