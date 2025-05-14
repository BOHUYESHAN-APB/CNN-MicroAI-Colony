import { describe, it, expect, beforeEach } from '@jest/globals';
import { renderHook } from '@testing-library/react-hooks';
import { useTranslation } from 'react-i18next';
import {
  changeLanguage,
  getCurrentLanguage,
  translate,
  mockTranslation,
  clearMocks
} from '../test-utils';

describe('i18n utilities', () => {
  beforeEach(() => {
    clearMocks();
  });

  describe('Language switching', () => {
    it('should switch between Chinese and English', async () => {
      // Test Chinese
      await changeLanguage('zh-CN');
      expect(getCurrentLanguage()).toBe('zh-CN');
      expect(translate('settings.camera.title')).toBe('相机设置');
      
      // Test English
      await changeLanguage('en-US');
      expect(getCurrentLanguage()).toBe('en-US');
      expect(translate('settings.camera.title')).toBe('Camera Settings');
    });

    it('should work with translation hooks', () => {
      const { result } = renderHook(() => useTranslation());

      result.current.i18n.changeLanguage('zh-CN');
      expect(result.current.t('common.save')).toBe('保存');

      result.current.i18n.changeLanguage('en-US');
      expect(result.current.t('common.save')).toBe('Save');
    });
  });

  describe('Translation mocking', () => {
    it('should allow mocking specific translations', () => {
      const mockT = mockTranslation('custom.key', '自定义值', 'zh-CN');
      expect(mockT('custom.key')).toBe('自定义值');
      expect(getCurrentLanguage()).toBe('zh-CN');
    });

    it('should handle nested translation keys', () => {
      expect(translate('settings.camera.fps', 'zh-CN')).toBe('帧率');
      expect(translate('settings.camera.fps', 'en-US')).toBe('Frame Rate');
    });

    it('should fallback to English when translation is missing', () => {
      const key = 'nonexistent.key';
      expect(translate(key, 'zh-CN')).toBe(key);
      expect(translate(key, 'en-US')).toBe(key);
    });
  });

  describe('Translation hook behavior', () => {
    it('should maintain language preference', () => {
      const { result: result1 } = renderHook(() => useTranslation());
      const { result: result2 } = renderHook(() => useTranslation());

      // Change language in first hook
      result1.current.i18n.changeLanguage('en-US');

      // Second hook should reflect the change
      expect(result2.current.i18n.language).toBe('en-US');
      expect(result2.current.t('common.save')).toBe('Save');
    });

    it('should update all components when language changes', () => {
      const { result } = renderHook(() => useTranslation());

      // Test Chinese
      result.current.i18n.changeLanguage('zh-CN');
      expect(result.current.t('common.confirm')).toBe('确认');
      expect(result.current.t('settings.camera.resolution')).toBe('分辨率');

      // Test English
      result.current.i18n.changeLanguage('en-US');
      expect(result.current.t('common.confirm')).toBe('Confirm');
      expect(result.current.t('settings.camera.resolution')).toBe('Resolution');
    });
  });
});
