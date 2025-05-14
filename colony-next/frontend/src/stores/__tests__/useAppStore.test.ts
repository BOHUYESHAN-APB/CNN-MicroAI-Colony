import { renderHook } from '@testing-library/react-hooks';
import { describe, it, expect, jest, beforeEach } from '@jest/globals';
import { useAppStore } from '../useAppStore';

// Mock i18n
jest.mock('../../i18n', () => ({
  changeLanguage: jest.fn()
}));

describe('useAppStore', () => {
  beforeEach(() => {
    // Clear the store before each test
    const { resetSettings } = useAppStore.getState();
    resetSettings();
    jest.clearAllMocks();
  });

  describe('camera settings', () => {
    it('should update camera settings', () => {
      const { result } = renderHook(() => useAppStore());
      
      result.current.setCameraSettings({
        resolution: '1280x720',
        fps: 60
      });

      expect(result.current.camera).toMatchObject({
        resolution: '1280x720',
        fps: 60
      });
    });
  });

  describe('analysis settings', () => {
    it('should update analysis settings', () => {
      const { result } = renderHook(() => useAppStore());

      result.current.setAnalysisSettings({
        confidenceThreshold: 0.8,
        minColonySize: 15
      });

      expect(result.current.analysis).toMatchObject({
        confidenceThreshold: 0.8,
        minColonySize: 15
      });
    });
  });

  describe('UI settings', () => {
    it('should update UI settings', () => {
      const { result } = renderHook(() => useAppStore());

      result.current.setUiSettings({
        darkMode: true,
        showGrid: false
      });

      expect(result.current.ui).toMatchObject({
        darkMode: true,
        showGrid: false
      });
    });

    it('should change language and update i18n', () => {
      const { result } = renderHook(() => useAppStore());
      const mockI18n = require('../../i18n');

      result.current.setLanguage('en-US');

      expect(result.current.ui.language).toBe('en-US');
      expect(mockI18n.changeLanguage).toHaveBeenCalledWith('en-US');
    });
  });

  describe('reset settings', () => {
    it('should reset all settings to initial values', () => {
      const { result } = renderHook(() => useAppStore());

      result.current.setCameraSettings({ zoom: 2.0 });
      result.current.setUiSettings({ darkMode: true });

      result.current.resetSettings();

      expect(result.current.camera.zoom).toBe(1.0);
      expect(result.current.ui.darkMode).toBe(false);
    });
  });
});
