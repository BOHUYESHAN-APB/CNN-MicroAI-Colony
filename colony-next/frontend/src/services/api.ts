import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';
const WS_BASE_URL = 'ws://localhost:8000';

// 创建axios实例
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
});

// 定义API接口
export interface AnalysisResult {
  colonies: Array<{
    position: [number, number];
    size: number;
    confidence: number;
  }>;
  count: number;
  tilt: [number, number];
}

export interface CameraSettings {
  resolution: string;
  fps: number;
}

export interface SystemSettings {
  camera: CameraSettings;
  analysis: {
    confidence_threshold: number;
    min_colony_size: number;
  };
}

// API方法
export const apiService = {
  // 健康检查
  async checkHealth() {
    const response = await api.get('/');
    return response.data;
  },

  // 分析图片
  async analyzeImage(file: File) {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post<{
      status: string;
      results: AnalysisResult;
    }>('/analyze', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    return response.data;
  },

  // 相机校准
  async calibrateCamera(file: File) {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/calibrate', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    return response.data;
  },

  // 获取设置
  async getSettings() {
    const response = await api.get<SystemSettings>('/settings');
    return response.data;
  },

  // 更新设置
  async updateSettings(settings: Partial<SystemSettings>) {
    const response = await api.post('/settings', settings);
    return response.data;
  },

  // 批量分析
  async batchAnalyze(files: File[]) {
    const formData = new FormData();
    files.forEach(file => {
      formData.append('files', file);
    });
    const response = await api.post('/batch', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    return response.data;
  },

  // 获取可用模型
  async getModels() {
    const response = await api.get('/models');
    return response.data;
  },

  // 设置当前模型
  async setModel(modelName: string) {
    const response = await api.post(`/models/${modelName}`);
    return response.data;
  }
};

// WebSocket连接管理
export class WebSocketManager {
  private cameraWs: WebSocket | null = null;
  private analysisWs: WebSocket | null = null;
  private cameraCallback: ((data: any) => void) | null = null;
  private analysisCallback: ((data: any) => void) | null = null;

  // 连接相机WebSocket
  connectCamera(onMessage: (data: any) => void) {
    if (this.cameraWs) {
      this.cameraWs.close();
    }
    
    this.cameraWs = new WebSocket(`${WS_BASE_URL}/ws/camera`);
    this.cameraCallback = onMessage;
    
    this.cameraWs.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (this.cameraCallback) {
        this.cameraCallback(data);
      }
    };
    
    this.cameraWs.onerror = (error) => {
      console.error('Camera WebSocket error:', error);
    };
  }

  // 连接分析WebSocket
  connectAnalysis(onMessage: (data: any) => void) {
    if (this.analysisWs) {
      this.analysisWs.close();
    }
    
    this.analysisWs = new WebSocket(`${WS_BASE_URL}/ws/analysis`);
    this.analysisCallback = onMessage;
    
    this.analysisWs.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (this.analysisCallback) {
        this.analysisCallback(data);
      }
    };
    
    this.analysisWs.onerror = (error) => {
      console.error('Analysis WebSocket error:', error);
    };
  }

  // 断开所有连接
  disconnect() {
    if (this.cameraWs) {
      this.cameraWs.close();
      this.cameraWs = null;
    }
    if (this.analysisWs) {
      this.analysisWs.close();
      this.analysisWs = null;
    }
  }
}

// 创建WebSocket管理器实例
export const wsManager = new WebSocketManager();
