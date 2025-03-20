import pytest
import numpy as np
from dataclasses import is_dataclass
from apps.app.core.models.image_data import ImageData

@pytest.fixture
def sample_image():
    return np.zeros((100, 100, 3), dtype=np.uint8)

def test_image_data_initialization(sample_image):
    """测试ImageData模型初始化"""
    metadata = {"source": "test"}
    image_data = ImageData(
        original=sample_image,
        path="/test/path.jpg",
        metadata=metadata
    )
    
    assert image_data.original.shape == (100, 100, 3)
    assert image_data.path == "/test/path.jpg"
    assert image_data.metadata["source"] == "test"
    assert image_data.parent is None
    assert is_dataclass(image_data)

def test_processing_history(sample_image):
    """测试处理历史追溯功能"""
    # 创建处理历史链
    root = ImageData(sample_image, "/root.jpg", {})
    child1 = ImageData(sample_image, "/root.jpg", {}, parent=root)
    child2 = ImageData(sample_image, "/root.jpg", {}, parent=child1)
    
    history = child2.processing_history
    assert len(history) == 3
    assert history[0] == root
    assert history[-1] == child2

def test_metadata_access(sample_image):
    """测试元数据访问方法"""
    metadata = {"width": 100, "height": 100}
    image_data = ImageData(sample_image, "/test.jpg", metadata)
    
    assert image_data.get_metadata_field("width") == 100
    assert image_data.get_metadata_field("invalid", "default") == "default"

def test_current_image_property(sample_image):
    """测试current_image属性"""
    modified_image = sample_image.copy()
    modified_image[50:,:50] = 255
    
    image_data = ImageData(modified_image, "/test.jpg", {})
    assert np.array_equal(image_data.current_image, modified_image)
    assert id(image_data.current_image) == id(modified_image)
