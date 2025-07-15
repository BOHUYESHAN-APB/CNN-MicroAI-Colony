"""
测量精度验证工具
用于验证抑菌圈检测结果的准确性
"""
import cv2
import numpy as np
import logging
from typing import List, Dict, Tuple, Optional
from pathlib import Path
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class AccuracyValidator:
    """测量精度验证器"""
    
    def __init__(self):
        self.ground_truth_data = {}
        self.validation_results = []
        
    def load_ground_truth(self, ground_truth_file: str) -> bool:
        """加载标准答案数据"""
        try:
            if Path(ground_truth_file).exists():
                with open(ground_truth_file, 'r', encoding='utf-8') as f:
                    self.ground_truth_data = json.load(f)
                logger.info(f"已加载标准答案数据: {len(self.ground_truth_data)} 个文件")
                return True
            else:
                logger.warning(f"标准答案文件不存在: {ground_truth_file}")
                return False
        except Exception as e:
            logger.error(f"加载标准答案失败: {e}")
            return False
    
    def save_ground_truth(self, ground_truth_file: str) -> bool:
        """保存标准答案数据"""
        try:
            with open(ground_truth_file, 'w', encoding='utf-8') as f:
                json.dump(self.ground_truth_data, f, indent=2, ensure_ascii=False)
            logger.info(f"标准答案已保存到: {ground_truth_file}")
            return True
        except Exception as e:
            logger.error(f"保存标准答案失败: {e}")
            return False
    
    def add_ground_truth(self, filename: str, dish_center: Tuple[int, int], 
                        dish_radius: int, substances: List[Dict], zones: List[Dict]):
        """添加标准答案数据"""
        self.ground_truth_data[filename] = {
            'dish': {
                'center': dish_center,
                'radius': dish_radius
            },
            'substances': substances,
            'zones': zones,
            'timestamp': datetime.now().isoformat()
        }
        logger.info(f"已添加标准答案: {filename}")
    
    def validate_detection_result(self, filename: str, detection_result: Dict) -> Dict:
        """验证检测结果的精度"""
        if filename not in self.ground_truth_data:
            return {
                'filename': filename,
                'status': 'no_ground_truth',
                'message': '没有找到对应的标准答案数据'
            }
        
        ground_truth = self.ground_truth_data[filename]
        validation_result = {
            'filename': filename,
            'status': 'validated',
            'timestamp': datetime.now().isoformat(),
            'dish_accuracy': self._validate_dish(detection_result.get('dish'), ground_truth['dish']),
            'substance_accuracy': self._validate_substances(detection_result.get('substances', []), ground_truth['substances']),
            'zone_accuracy': self._validate_zones(detection_result.get('zones', []), ground_truth['zones'])
        }
        
        # 计算总体精度
        validation_result['overall_accuracy'] = self._calculate_overall_accuracy(validation_result)
        
        self.validation_results.append(validation_result)
        return validation_result
    
    def _validate_dish(self, detected_dish: Optional[Dict], ground_truth_dish: Dict) -> Dict:
        """验证培养皿检测精度"""
        if not detected_dish:
            return {
                'detected': False,
                'center_error': float('inf'),
                'radius_error': float('inf'),
                'accuracy_score': 0.0
            }
        
        # 计算中心点误差
        gt_center = ground_truth_dish['center']
        det_center = detected_dish['center']
        center_error = np.sqrt((gt_center[0] - det_center[0])**2 + (gt_center[1] - det_center[1])**2)
        
        # 计算半径误差
        gt_radius = ground_truth_dish['radius']
        det_radius = detected_dish['radius']
        radius_error = abs(gt_radius - det_radius)
        radius_error_rate = radius_error / gt_radius if gt_radius > 0 else float('inf')
        
        # 计算精度得分（基于相对误差）
        center_score = max(0, 1 - center_error / gt_radius) if gt_radius > 0 else 0
        radius_score = max(0, 1 - radius_error_rate)
        accuracy_score = (center_score + radius_score) / 2
        
        return {
            'detected': True,
            'center_error': float(center_error),
            'radius_error': float(radius_error),
            'radius_error_rate': float(radius_error_rate),
            'center_score': float(center_score),
            'radius_score': float(radius_score),
            'accuracy_score': float(accuracy_score)
        }
    
    def _validate_substances(self, detected_substances: List[Dict], 
                           ground_truth_substances: List[Dict]) -> Dict:
        """验证抑菌物质检测精度"""
        gt_count = len(ground_truth_substances)
        det_count = len(detected_substances)
        
        if gt_count == 0 and det_count == 0:
            return {
                'precision': 1.0,
                'recall': 1.0,
                'f1_score': 1.0,
                'count_accuracy': 1.0,
                'position_accuracy': 1.0,
                'overall_score': 1.0
            }
        
        if gt_count == 0:
            return {
                'precision': 0.0 if det_count > 0 else 1.0,
                'recall': 1.0,
                'f1_score': 0.0,
                'count_accuracy': 0.0,
                'position_accuracy': 0.0,
                'overall_score': 0.0
            }
        
        if det_count == 0:
            return {
                'precision': 1.0,
                'recall': 0.0,
                'f1_score': 0.0,
                'count_accuracy': 0.0,
                'position_accuracy': 0.0,
                'overall_score': 0.0
            }
        
        # 计算最佳匹配
        matches = self._find_best_matches(detected_substances, ground_truth_substances)
        
        # 计算精确率、召回率和F1分数
        true_positives = len(matches)
        precision = true_positives / det_count if det_count > 0 else 0
        recall = true_positives / gt_count if gt_count > 0 else 0
        f1_score = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        
        # 计算数量精度
        count_accuracy = 1 - abs(det_count - gt_count) / max(det_count, gt_count)
        
        # 计算位置精度
        position_errors = []
        for det_idx, gt_idx in matches:
            det_center = detected_substances[det_idx]['center']
            gt_center = ground_truth_substances[gt_idx]['center']
            error = np.sqrt((det_center[0] - gt_center[0])**2 + (det_center[1] - gt_center[1])**2)
            position_errors.append(error)
        
        position_accuracy = 1 - (np.mean(position_errors) / 50) if position_errors else 0  # 假设50px为最大允许误差
        position_accuracy = max(0, min(1, position_accuracy))
        
        # 总体得分
        overall_score = (precision + recall + f1_score + count_accuracy + position_accuracy) / 5
        
        return {
            'precision': float(precision),
            'recall': float(recall),
            'f1_score': float(f1_score),
            'count_accuracy': float(count_accuracy),
            'position_accuracy': float(position_accuracy),
            'overall_score': float(overall_score),
            'matches': len(matches),
            'gt_count': gt_count,
            'det_count': det_count
        }
    
    def _validate_zones(self, detected_zones: List[Dict], ground_truth_zones: List[Dict]) -> Dict:
        """验证抑菌圈检测精度"""
        # 抑菌圈验证逻辑与物质类似，但重点关注直径精度
        gt_count = len(ground_truth_zones)
        det_count = len(detected_zones)
        
        if gt_count == 0 and det_count == 0:
            return {
                'precision': 1.0,
                'recall': 1.0,
                'f1_score': 1.0,
                'diameter_accuracy': 1.0,
                'overall_score': 1.0
            }
        
        if gt_count == 0 or det_count == 0:
            return {
                'precision': 0.0,
                'recall': 0.0,
                'f1_score': 0.0,
                'diameter_accuracy': 0.0,
                'overall_score': 0.0
            }
        
        # 计算最佳匹配
        matches = self._find_best_matches(detected_zones, ground_truth_zones)
        
        # 计算基础指标
        true_positives = len(matches)
        precision = true_positives / det_count if det_count > 0 else 0
        recall = true_positives / gt_count if gt_count > 0 else 0
        f1_score = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        
        # 计算直径精度
        diameter_errors = []
        for det_idx, gt_idx in matches:
            det_diameter = detected_zones[det_idx].get('diameter_mm', 0)
            gt_diameter = ground_truth_zones[gt_idx].get('diameter_mm', 0)
            if gt_diameter > 0:
                error_rate = abs(det_diameter - gt_diameter) / gt_diameter
                diameter_errors.append(error_rate)
        
        diameter_accuracy = 1 - np.mean(diameter_errors) if diameter_errors else 0
        diameter_accuracy = max(0, min(1, diameter_accuracy))
        
        # 总体得分
        overall_score = (precision + recall + f1_score + diameter_accuracy) / 4
        
        return {
            'precision': float(precision),
            'recall': float(recall),
            'f1_score': float(f1_score),
            'diameter_accuracy': float(diameter_accuracy),
            'overall_score': float(overall_score),
            'matches': len(matches),
            'gt_count': gt_count,
            'det_count': det_count
        }
    
    def _find_best_matches(self, detected_items: List[Dict], 
                          ground_truth_items: List[Dict], max_distance: float = 50.0) -> List[Tuple[int, int]]:
        """找到检测结果与标准答案的最佳匹配"""
        matches = []
        used_gt_indices = set()
        
        # 计算所有检测结果与标准答案的距离
        distances = []
        for i, det_item in enumerate(detected_items):
            for j, gt_item in enumerate(ground_truth_items):
                det_center = det_item['center']
                gt_center = gt_item['center']
                distance = np.sqrt((det_center[0] - gt_center[0])**2 + (det_center[1] - gt_center[1])**2)
                distances.append((distance, i, j))
        
        # 按距离排序，贪心匹配
        distances.sort()
        for distance, det_idx, gt_idx in distances:
            if distance <= max_distance and gt_idx not in used_gt_indices:
                matches.append((det_idx, gt_idx))
                used_gt_indices.add(gt_idx)
        
        return matches
    
    def _calculate_overall_accuracy(self, validation_result: Dict) -> float:
        """计算总体精度"""
        dish_score = validation_result['dish_accuracy']['accuracy_score']
        substance_score = validation_result['substance_accuracy']['overall_score']
        zone_score = validation_result['zone_accuracy']['overall_score']
        
        # 加权平均（培养皿检测权重较高）
        overall_accuracy = (dish_score * 0.4 + substance_score * 0.3 + zone_score * 0.3)
        return float(overall_accuracy)
    
    def generate_accuracy_report(self, output_file: str = None) -> str:
        """生成精度验证报告"""
        if not self.validation_results:
            return "没有验证结果可供生成报告"
        
        report_lines = []
        report_lines.append("=== 测量精度验证报告 ===\n")
        report_lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"验证文件数: {len(self.validation_results)}\n")
        
        # 总体统计
        overall_accuracies = [r['overall_accuracy'] for r in self.validation_results]
        dish_accuracies = [r['dish_accuracy']['accuracy_score'] for r in self.validation_results]
        substance_accuracies = [r['substance_accuracy']['overall_score'] for r in self.validation_results]
        zone_accuracies = [r['zone_accuracy']['overall_score'] for r in self.validation_results]
        
        report_lines.append("总体统计:")
        report_lines.append(f"  平均总体精度: {np.mean(overall_accuracies):.3f}")
        report_lines.append(f"  平均培养皿精度: {np.mean(dish_accuracies):.3f}")
        report_lines.append(f"  平均物质检测精度: {np.mean(substance_accuracies):.3f}")
        report_lines.append(f"  平均抑菌圈精度: {np.mean(zone_accuracies):.3f}\n")
        
        # 详细结果
        report_lines.append("详细验证结果:")
        report_lines.append("-" * 80)
        
        for result in self.validation_results:
            report_lines.append(f"\n文件: {result['filename']}")
            report_lines.append(f"  总体精度: {result['overall_accuracy']:.3f}")
            
            # 培养皿精度
            dish = result['dish_accuracy']
            if dish['detected']:
                report_lines.append(f"  培养皿检测: ✅ 精度{dish['accuracy_score']:.3f}")
                report_lines.append(f"    中心误差: {dish['center_error']:.1f}px")
                report_lines.append(f"    半径误差: {dish['radius_error']:.1f}px ({dish['radius_error_rate']*100:.1f}%)")
            else:
                report_lines.append(f"  培养皿检测: ❌ 未检测到")
            
            # 物质检测精度
            substance = result['substance_accuracy']
            report_lines.append(f"  物质检测: 精确率{substance['precision']:.3f}, 召回率{substance['recall']:.3f}")
            report_lines.append(f"    检测数量: {substance['det_count']}, 标准数量: {substance['gt_count']}, 匹配: {substance['matches']}")
            
            # 抑菌圈精度
            zone = result['zone_accuracy']
            report_lines.append(f"  抑菌圈检测: 精确率{zone['precision']:.3f}, 召回率{zone['recall']:.3f}")
            report_lines.append(f"    直径精度: {zone['diameter_accuracy']:.3f}")
        
        report_content = "\n".join(report_lines)
        
        # 保存报告
        if output_file:
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(report_content)
                logger.info(f"精度验证报告已保存到: {output_file}")
            except Exception as e:
                logger.error(f"保存报告失败: {e}")
        
        return report_content
    
    def get_accuracy_statistics(self) -> Dict:
        """获取精度统计数据"""
        if not self.validation_results:
            return {}
        
        overall_accuracies = [r['overall_accuracy'] for r in self.validation_results]
        dish_accuracies = [r['dish_accuracy']['accuracy_score'] for r in self.validation_results]
        substance_accuracies = [r['substance_accuracy']['overall_score'] for r in self.validation_results]
        zone_accuracies = [r['zone_accuracy']['overall_score'] for r in self.validation_results]
        
        return {
            'overall_accuracy': {
                'mean': float(np.mean(overall_accuracies)),
                'std': float(np.std(overall_accuracies)),
                'min': float(np.min(overall_accuracies)),
                'max': float(np.max(overall_accuracies))
            },
            'dish_accuracy': {
                'mean': float(np.mean(dish_accuracies)),
                'std': float(np.std(dish_accuracies)),
                'min': float(np.min(dish_accuracies)),
                'max': float(np.max(dish_accuracies))
            },
            'substance_accuracy': {
                'mean': float(np.mean(substance_accuracies)),
                'std': float(np.std(substance_accuracies)),
                'min': float(np.min(substance_accuracies)),
                'max': float(np.max(substance_accuracies))
            },
            'zone_accuracy': {
                'mean': float(np.mean(zone_accuracies)),
                'std': float(np.std(zone_accuracies)),
                'min': float(np.min(zone_accuracies)),
                'max': float(np.max(zone_accuracies))
            },
            'validation_count': len(self.validation_results)
        }

def create_sample_ground_truth():
    """创建示例标准答案数据"""
    validator = AccuracyValidator()
    
    # 添加示例标准答案
    validator.add_ground_truth(
        "OIP-C.jpg",
        dish_center=(239, 232),
        dish_radius=184,
        substances=[
            {'center': (221, 221), 'radius': 17, 'type': 'hole'},
            {'center': (334, 245), 'radius': 17, 'type': 'hole'},
            {'center': (248, 323), 'radius': 11, 'type': 'hole'},
            {'center': (356, 282), 'radius': 9, 'type': 'hole'}
        ],
        zones=[
            {'center': (221, 221), 'radius': 45, 'diameter_mm': 22.0},
            {'center': (334, 245), 'radius': 38, 'diameter_mm': 18.5},
            {'center': (248, 323), 'radius': 35, 'diameter_mm': 17.1},
            {'center': (356, 282), 'radius': 30, 'diameter_mm': 14.7}
        ]
    )
    
    validator.add_ground_truth(
        "R-C.jpg",
        dish_center=(549, 241),
        dish_radius=237,
        substances=[
            {'center': (562, 288), 'radius': 25, 'type': 'filter_paper'},
            {'center': (450, 200), 'radius': 23, 'type': 'filter_paper'},
            {'center': (620, 180), 'radius': 24, 'type': 'filter_paper'}
        ],
        zones=[
            {'center': (562, 288), 'radius': 55, 'diameter_mm': 20.8},
            {'center': (450, 200), 'radius': 48, 'diameter_mm': 18.2},
            {'center': (620, 180), 'radius': 52, 'diameter_mm': 19.7}
        ]
    )
    
    return validator

if __name__ == "__main__":
    # 创建示例标准答案
    validator = create_sample_ground_truth()
    validator.save_ground_truth("test_ground_truth.json")
    print("示例标准答案已创建并保存到 test_ground_truth.json")