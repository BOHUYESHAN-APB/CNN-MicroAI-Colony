import pytest
from unittest.mock import MagicMock, patch, call
import numpy as np
from apps.app.core.services.image_processor import ImageProcessor
from apps.app.core.models.image_data import ImageData

@pytest.fixture
def image_processor():
    return ImageProcessor()

@pytest.fixture
def mock_image():
    return np.zeros((100, 100, 3), dtype=np.uint8)

@pytest.mark.asyncio
async def test_image_processing_flow(image_processor, mock_image):
    """测试完整的图像处理流程"""
    # Mock依赖项
    mock_step1 = MagicMock(return_value=mock_image)
    mock_step2 = MagicMock(return_value=mock_image + 50)
    
    # 配置processor
    image_processor.load_image("dummy.jpg")
    image_processor.add_processing_step(mock_step1)
    image_processor.add_processing_step(mock_step2)
    
    # 执行处理
    await image_processor.process_image()
    
    # 验证
    assert len(image_processor._processing_stack) == 2
    mock_step1.assert_called_once()
    mock_step2.assert_called_once()
    assert isinstance(image_processor._processing_stack[-1], ImageData)

def test_load_image_success(image_processor, mock_image):
    """测试成功加载图像"""
    test_path = "/test/path.jpg"
    with patch('cv2.imdecode', return_value=mock_image) as mock_imdecode, \
         patch('os.path.abspath', return_value=test_path), \
         patch('os.path.getsize'), \
         patch('os.path.getctime'), \
         patch('os.path.getmtime'):
        
        result = image_processor.load_image("any.jpg")
        
        assert result is True
        mock_imdecode.assert_called_once()
        assert image_processor._current_image.path == test_path

def test_load_image_failure(image_processor):
    """测试图像加载失败情况"""
    with patch('cv2.imdecode', return_value=None):
        result = image_processor.load_image("invalid.jpg")
        assert result is False

@pytest.mark.asyncio
async def test_processing_without_image(image_processor):
    """测试无图像时的处理流程"""
    with patch.object(image_processor._logger, 'warning') as mock_warning:
        await image_processor.process_image()
        mock_warning.assert_called_with("无可用图像进行处理")

def test_processing_step_management(image_processor):
    """测试处理步骤管理"""
    def sample_step(img):
        return img.original
    
    image_processor.add_processing_step(sample_step)
    assert len(image_processor._pipeline) == 1
    assert image_processor._pipeline[0].__name__ == "sample_step"

@pytest.mark.asyncio
async def test_error_handling(image_processor, mock_image):
    """测试异常处理机制"""
    def faulty_step(img):
        raise ValueError("模拟错误")
    
    image_processor.load_image("dummy.jpg")
    image_processor.add_processing_step(faulty_step)
    
    with pytest.raises(ValueError) as excinfo:
        await image_processor.process_image()
    
    assert "模拟错误" in str(excinfo.value)
