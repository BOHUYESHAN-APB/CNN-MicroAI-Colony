import cv2
import numpy as np
import math
import os
import uuid
from typing import List, Optional, Tuple, Dict
from enum import Enum
from .models import Colony, PetriDish  # Assuming models.py defines these dataclasses
from .processor import ImageProcessor, ImageQuality
from utils.logger import get_logger
from utils.config import Config

CFG = Config.default()

logger = get_logger(__name__)


class DetectionMode(Enum):
    SINGLE_SUBSTANCE = 1
    MULTIPLE_SUBSTANCES = 2
    UNKNOWN = 0


class SubstanceType(Enum):
    FILTER_PAPER = 1
    HOLE = 2
    UNKNOWN = 0


class CircleDetector:
    """圆形检测器类，用于检测培养皿、抑菌物质（滤纸片/孔洞）和抑菌圈"""

    def __init__(self, plate_diameter_mm: float = 90.0,
                 filter_paper_diameter_mm: float = 6.0,
                 hole_diameter_mm: float = 6.0):
        self.plate_diameter_mm = plate_diameter_mm
        self.filter_paper_diameter_mm = filter_paper_diameter_mm
        self.hole_diameter_mm = hole_diameter_mm
        self.processor = ImageProcessor()
        self.px_per_mm = None  # 像素/毫米比例
        self.detection_mode = DetectionMode.UNKNOWN
        self.substance_type = SubstanceType.UNKNOWN
        self.detected_substances: List[Colony] = []

    def detect_petri_dishes(self, image: np.ndarray) -> List[PetriDish]:
        """检测培养皿并进行尺寸标定"""
        logger.info("开始检测培养皿")
        self.px_per_mm = None  # Reset px_per_mm for each new image processing

        # 预处理
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # 高斯模糊
        blurred = cv2.GaussianBlur(gray, (9, 9), 2)
        processed = self.processor.preprocess(blurred)

        params = {
            'dp': 1,
            'minDist': 400,
            'param1': 50,
            'param2': 35,
            'minRadius': int(image.shape[0] / 3),
            'maxRadius': int(image.shape[0] / 1.8)
        }

        # 培养皿检测
        circles = cv2.HoughCircles(
            processed,
            cv2.HOUGH_GRADIENT,
            **params
        )

        plates = []
        if circles is not None:
            circles = np.uint16(np.around(circles))
            for x, y, r in circles[0, :]:
                # 验证圆的有效性
                if self._validate_dish_circle(processed, (x, y), r):
                    plates.append(PetriDish(
                        center=(int(x), int(y)),
                        radius=int(r),
                        diameter_mm=self.plate_diameter_mm
                    ))
                    # 更新像素比例
                    self.px_per_mm = r * 2 / self.plate_diameter_mm
                    logger.info(f"标定比例: {self.px_per_mm:.2f}px/mm")

        logger.info(f"检测到 {len(plates)} 个培养皿")
        return plates

    def analyze_dish_contents(self, image: np.ndarray, dish: PetriDish) -> Tuple[DetectionMode, SubstanceType, List[Colony]]:
        """
        分析培养皿内容，判断是单个/多个抑菌物质，以及物质类型（滤纸片/孔洞）。
        """
        logger.info(f"开始分析培养皿 {dish.center} 内的物质...")
        if self.px_per_mm is None:
            logger.error("px_per_mm 未标定，无法分析培养皿内容。")
            return DetectionMode.UNKNOWN, SubstanceType.UNKNOWN, []

        papers = self._detect_substances_by_type(image, dish, SubstanceType.FILTER_PAPER)
        holes = self._detect_substances_by_type(image, dish, SubstanceType.HOLE)

        detected_substances = []
        final_substance_type = SubstanceType.UNKNOWN
        detection_mode = DetectionMode.UNKNOWN

        if len(papers) > 0 and len(holes) == 0:
            detected_substances = papers
            final_substance_type = SubstanceType.FILTER_PAPER
            logger.info(f"主要检测到滤纸片: {len(papers)} 个")
        elif len(holes) > 0 and len(papers) == 0:
            detected_substances = holes
            final_substance_type = SubstanceType.HOLE
            logger.info(f"主要检测到孔洞: {len(holes)} 个")
        elif len(papers) > 0 and len(holes) > 0:
            logger.warning(f"同时检测到 {len(papers)} 个滤纸片和 {len(holes)} 个孔洞。优先考虑数量较多者或滤纸片。")
            if len(papers) >= len(holes):
                detected_substances = papers
                final_substance_type = SubstanceType.FILTER_PAPER
            else:
                detected_substances = holes
                final_substance_type = SubstanceType.HOLE
        else:
            logger.warning("未能明确检测到滤纸片或孔洞。")

        if len(detected_substances) == 1:
            detection_mode = DetectionMode.SINGLE_SUBSTANCE
        elif len(detected_substances) > 1:
            detection_mode = DetectionMode.MULTIPLE_SUBSTANCES
        else:  # len == 0
            logger.info("未检测到明确的抑菌物质，可能为单一抑菌圈在中心。")
            detection_mode = DetectionMode.SINGLE_SUBSTANCE
            final_substance_type = SubstanceType.UNKNOWN

        self.detection_mode = detection_mode
        self.substance_type = final_substance_type
        self.detected_substances = detected_substances

        logger.info(f"分析完成: 模式={detection_mode.name}, 类型={final_substance_type.name}, 数量={len(detected_substances)}")
        return detection_mode, final_substance_type, detected_substances

    def _detect_substances_by_type(self, image: np.ndarray, dish: PetriDish, substance_type: SubstanceType) -> List[Colony]:
        """
        根据指定的物质类型检测圆形物质（滤纸片或孔洞）。
        """
        if self.px_per_mm is None:
            raise ValueError("请先进行培养皿检测和尺寸标定")

        logger.info(f"开始检测 {substance_type.name}")

        dish_mask = np.zeros(image.shape[:2], dtype=np.uint8)
        cv2.circle(dish_mask, dish.center, dish.radius, 255, -1)

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        masked_dish_gray = cv2.bitwise_and(gray, gray, mask=dish_mask)

        # Default params
        hough_param2_val = 25
        brightness_threshold_val = 150
        max_std_dev_val = 30.0
        check_roi_bright = True
        radius_factor_min = 0.6
        radius_factor_max = 1.4

        if substance_type == SubstanceType.FILTER_PAPER:
            diameter_mm = self.filter_paper_diameter_mm
            processed_for_hough = self.processor.preprocess(masked_dish_gray)
            hough_param2_val = 28
            brightness_threshold_val = 120
            max_std_dev_val = 25.0
            check_roi_bright = True
            if self.px_per_mm and self.px_per_mm > 0:
                radius_factor_min = 0.85
                radius_factor_max = 1.15
        elif substance_type == SubstanceType.HOLE:
            diameter_mm = self.hole_diameter_mm
            inverted_gray = cv2.bitwise_not(masked_dish_gray)
            inverted_dish_roi = cv2.bitwise_and(inverted_gray, inverted_gray, mask=dish_mask)
            # If a dark_blob profile specifies preprocessing params, use them
            try:
                profile = CFG.profiles.get('dark_blob', {})
                tk = tuple(profile.get('tophat_kernel', (15, 15)))
                clahe_clip = float(profile.get('clahe_clip', self.processor.clahe_clip_limit))
            except Exception:
                tk = (15, 15)
                clahe_clip = self.processor.clahe_clip_limit
            # temporarily set clahe for preprocess_for_hole
            old_clip = getattr(self.processor, 'clahe_clip_limit', 2.0)
            self.processor.clahe_clip_limit = clahe_clip
            processed_for_hough = self.processor.preprocess_for_hole(inverted_dish_roi, tophat_kernel=tk)
            # restore
            self.processor.clahe_clip_limit = old_clip
            hough_param1_val_for_hole = 40
            hough_param2_val = 8
            brightness_threshold_val = 90
            max_std_dev_val = 35.0
            check_roi_bright = False
            if self.px_per_mm and self.px_per_mm > 0:
                radius_factor_min = 0.7
                radius_factor_max = 1.3
        else:
            return []

        # Calculate expected radius in pixels
        if diameter_mm > 0 and self.px_per_mm and self.px_per_mm > 0:
            expected_radius_px = int(diameter_mm * self.px_per_mm / 2)
            min_radius_px = max(5, int(expected_radius_px * radius_factor_min))
            max_radius_px = int(expected_radius_px * radius_factor_max)
            min_dist_hough = max(int(expected_radius_px * 1.8), 20)
            logger.info(f"进行 {substance_type.name} 检测: 预期半径 {expected_radius_px}px, 范围 [{min_radius_px}-{max_radius_px}]px, param2={hough_param2_val}")
        else:
            logger.warning(f"px_per_mm ({self.px_per_mm}) 或物质直径 ({diameter_mm}mm) 无效，无法精确计算 {substance_type.name} 的预期像素半径。将使用较宽松的像素范围。")
            if substance_type == SubstanceType.FILTER_PAPER:
                min_radius_px = 8
                max_radius_px = 40
            elif substance_type == SubstanceType.HOLE:
                min_radius_px = 5
                max_radius_px = 35
            else:
                return []
            min_dist_hough = max(int(min_radius_px * 2.5), 20)
            logger.info(f"回退 {substance_type.name} 检测: 范围 [{min_radius_px}-{max_radius_px}]px, param2={hough_param2_val}")

        if min_radius_px <= 0 or max_radius_px <= 0 or min_radius_px >= max_radius_px:
            logger.warning(f"计算得到的最小半径({min_radius_px})或最大半径({max_radius_px})无效 for {substance_type.name}。跳过检测。")
            return []

        # Run Hough
        circles = cv2.HoughCircles(
            processed_for_hough,
            cv2.HOUGH_GRADIENT,
            dp=1.2,
            minDist=min_dist_hough,
            param1=hough_param1_val_for_hole if substance_type == SubstanceType.HOLE else 60,
            param2=hough_param2_val,
            minRadius=min_radius_px,
            maxRadius=max_radius_px
        )

        detected_items: List[Colony] = []

        if circles is not None:
            circles = np.uint16(np.around(circles))
            for x_u16, y_u16, r_u16 in circles[0, :]:
                x, y, r = int(x_u16), int(y_u16), int(r_u16)
                dish_center_x, dish_center_y = int(dish.center[0]), int(dish.center[1])
                distance_to_center = np.sqrt((x - dish_center_x) ** 2 + (y - dish_center_y) ** 2)
                if distance_to_center + r > dish.radius:
                    continue

                validation_context = f"{substance_type.name} candidate"
                if self._is_specular_spot(masked_dish_gray, (x, y), r):
                    logger.debug(f"{validation_context} at ({x},{y}) R={r} 被判定为高光/小斑点，跳过。")
                    continue

                if self._validate_roi_brightness(
                    image_gray=masked_dish_gray,
                    center=(x, y),
                    radius=r,
                    brightness_threshold=brightness_threshold_val,
                    max_std_dev=max_std_dev_val,
                    check_bright=check_roi_bright,
                    context=validation_context
                ):
                    detected_items.append(Colony(
                        center=(int(x), int(y)),
                        radius=int(r),
                        contour=self._create_circle_contour((x, y), r),
                        substance_type=substance_type
                    ))

        # Fallback for HOLE when Hough found nothing
        if substance_type == SubstanceType.HOLE and len(detected_items) == 0:
            logger.info("Hough 未检测到 HOLE，尝试备选检测")
            try:
                fallback_input = processed_for_hough if 'processed_for_hough' in locals() else masked_dish_gray

                # 判断是否暗底：如果是暗底，优先尝试 blob 检测（SimpleBlob）
                try:
                    is_dark = self._is_dark_background(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY), dish_mask)
                except Exception:
                    is_dark = False

                if is_dark:
                    logger.info("检测到暗背景，优先使用 blob 检测")
                    blob_res = self._detect_holes_by_blob(fallback_input, dish, min_radius_px, max_radius_px)
                    if blob_res:
                        logger.info(f"Blob 方法检测到 {len(blob_res)} 个 HOLE 候选")
                        detected_items.extend(blob_res)
                # 如果 blob 没有结果，或非暗底，则使用自适应阈值备选
                if len(detected_items) == 0:
                    logger.info("尝试自适应阈值+轮廓备选检测")
                    fallback = self._detect_holes_by_adaptive_threshold(fallback_input, dish, min_radius_px, max_radius_px)
                    if fallback:
                        logger.info(f"自适应轮廓方法检测到 {len(fallback)} 个 HOLE 候选")
                        detected_items.extend(fallback)
            except Exception as e:
                logger.exception(f"备选检测失败: {e}")

        logger.info(f"检测到 {len(detected_items)} 个 {substance_type.name}")
        return detected_items

    def _detect_holes_by_adaptive_threshold(self, image_gray: np.ndarray, dish: PetriDish,
                                           min_radius_px: int, max_radius_px: int) -> List[Colony]:
        """
        当 Hough 检测失败时的备选策略：使用自适应阈值或局部 Otsu + 轮廓检测来寻找透明孔洞（暗区）。
        返回 Colony 列表（可能为空）。
        """
        results: List[Colony] = []

        try:
            block_size = 31 if min(image_gray.shape[:2]) > 100 else 15
            adaptive = cv2.adaptiveThreshold(image_gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                             cv2.THRESH_BINARY_INV, block_size, 8)

            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            opened = cv2.morphologyEx(adaptive, cv2.MORPH_OPEN, kernel, iterations=1)
            closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel, iterations=1)

            contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # 保存中间调试图像（如果 debug_dir 被设置）
            try:
                if hasattr(self, 'debug_dir') and self.debug_dir:
                    os.makedirs(self.debug_dir, exist_ok=True)
                    uid = str(uuid.uuid4())[:8]
                    # Save preprocessed, adaptive mask, opened, closed
                    pre_fn = os.path.join(self.debug_dir, f"preproc_{uid}.png")
                    adapt_fn = os.path.join(self.debug_dir, f"adaptive_{uid}.png")
                    opened_fn = os.path.join(self.debug_dir, f"opened_{uid}.png")
                    closed_fn = os.path.join(self.debug_dir, f"closed_{uid}.png")
                    cv2.imwrite(pre_fn, image_gray)
                    cv2.imwrite(adapt_fn, adaptive)
                    cv2.imwrite(opened_fn, opened)
                    cv2.imwrite(closed_fn, closed)
            except Exception:
                logger.debug("保存 debug 中间图像失败，但继续处理")

            for contour in contours:
                area = cv2.contourArea(contour)
                if area <= 0:
                    continue

                perimeter = cv2.arcLength(contour, True)
                if perimeter == 0:
                    continue

                circularity = 4 * np.pi * area / (perimeter * perimeter)

                (cx, cy), radius = cv2.minEnclosingCircle(contour)
                cx_i, cy_i, radius_i = int(cx), int(cy), int(radius)

                if radius_i < min_radius_px or radius_i > max_radius_px:
                    continue

                if area < np.pi * (max(3, min_radius_px * 0.5) ** 2):
                    continue

                if circularity < 0.35:
                    continue

                if self._is_specular_spot(image_gray, (cx_i, cy_i), radius_i):
                    continue

                if not self._validate_roi_brightness(image_gray, (cx_i, cy_i), radius_i,
                                                     brightness_threshold=120, max_std_dev=60,
                                                     check_bright=False, context='adaptive_hole'):
                    continue

                distance_to_center = np.sqrt((cx - dish.center[0]) ** 2 + (cy - dish.center[1]) ** 2)
                if distance_to_center + radius > dish.radius:
                    continue

                results.append(Colony(
                    center=(cx_i, cy_i),
                    radius=radius_i,
                    contour=contour,
                    substance_type=SubstanceType.HOLE
                ))

        except Exception as ex:
            logger.exception(f"adaptive hole detection error: {ex}")

        return results

    def _is_dark_background(self, image_gray_full: np.ndarray, dish_mask: np.ndarray, thresh: float = 80.0) -> bool:
        """
        判断图像背景（培养皿外部）是否偏暗，用于选择专用的检测策略。
        image_gray_full: 原始整图灰度
        dish_mask: 培养皿掩膜（255 内部，0 外部）
        返回 True 表示背景偏暗。
        """
        try:
            outside_pixels = image_gray_full[dish_mask == 0]
            if outside_pixels.size == 0:
                return False
            mean_out = float(np.mean(outside_pixels))
            return mean_out < thresh
        except Exception:
            return False

    def _detect_holes_by_blob(self, image_gray: np.ndarray, dish: PetriDish,
                               min_radius_px: int, max_radius_px: int) -> List[Colony]:
        """
        使用 SimpleBlobDetector 在增强图像上检测亮斑（适用于将孔洞变为亮斑的预处理图），
        对检测到的 keypoints 做半径/位置过滤并返回 Colony 列表。
        """
        results: List[Colony] = []
        try:
            # 参数配置：按像素面积与圆度等筛选
            params = cv2.SimpleBlobDetector_Params()
            params.minThreshold = 5
            params.maxThreshold = 255
            params.filterByArea = True
            # try to use tuned profile if available
            try:
                profile = CFG.profiles.get('dark_blob', None)
            except Exception:
                profile = None

            if profile is not None:
                params.minArea = int(profile.get('minArea', max(10, np.pi * (min_radius_px * 0.5) ** 2)))
                params.maxArea = int(profile.get('maxArea', np.pi * (max_radius_px * 1.5) ** 2))
                params.filterByCircularity = True
                params.minCircularity = float(profile.get('minCircularity', 0.25))
                params.filterByInertia = True
                params.minInertiaRatio = float(profile.get('minInertiaRatio', 0.1))
                params.filterByConvexity = False
            else:
                params.minArea = max(10, int(np.pi * (min_radius_px * 0.5) ** 2))
                params.maxArea = int(np.pi * (max_radius_px * 1.5) ** 2)
                params.filterByCircularity = True
                params.minCircularity = 0.25
                params.filterByInertia = True
                params.minInertiaRatio = 0.1
                params.filterByConvexity = False

            detector = cv2.SimpleBlobDetector_create(params)

            keypoints = detector.detect(image_gray)
            for kp in keypoints:
                cx, cy = int(kp.pt[0]), int(kp.pt[1])
                # SimpleBlobDetector size is diameter
                r = int(kp.size / 2)

                # 验证在培养皿内
                dish_center_x, dish_center_y = int(dish.center[0]), int(dish.center[1])
                distance_to_center = np.sqrt((cx - dish_center_x) ** 2 + (cy - dish_center_y) ** 2)
                if distance_to_center + r > dish.radius:
                    continue

                if r < min_radius_px or r > max_radius_px:
                    continue

                # 使用原始增强图像验证亮度/均匀性（允许一定 std）
                if self._is_specular_spot(image_gray, (cx, cy), r):
                    continue

                results.append(Colony(
                    center=(cx, cy),
                    radius=r,
                    contour=self._create_circle_contour((cx, cy), r),
                    substance_type=SubstanceType.HOLE
                ))
        except Exception as ex:
            logger.exception(f"blob hole detection error: {ex}")

        return results
    def _is_specular_spot(self, image_gray: np.ndarray, center: Tuple[int, int], radius: int) -> bool:
        """
        简单判断一个候选是否为小的高光点或气泡：
        - 如果候选区域非常小且最大亮度远高于局部中值，则视为高光
        - 以像素差和面积为判定标准
        """
        x, y = center
        h, w = image_gray.shape[:2]
        r_check = max(1, int(radius))
        x1 = max(0, x - r_check)
        y1 = max(0, y - r_check)
        x2 = min(w, x + r_check)
        y2 = min(h, y + r_check)

        roi = image_gray[y1:y2, x1:x2]
        if roi.size == 0:
            return False

        max_val = np.max(roi)
        median_val = np.median(roi)
        area_px = roi.shape[0] * roi.shape[1]

        if area_px <= 50 and (max_val - median_val) > 100:
            return True

        return False

    def _validate_roi_brightness(self, image_gray: np.ndarray, center: Tuple[int, int], radius: int,
                                 brightness_threshold: float, max_std_dev: float,
                                 check_bright: bool = True, context: str = "") -> bool:
        """
        验证ROI区域的平均亮度是否符合预期，并且灰度标准差是否在允许范围内。
        check_bright=True: 检查是否足够亮 (如滤纸片)
        check_bright=False: 检查是否足够暗 (如孔洞在原图中)
        """
        x, y = center
        r_check_brightness = max(1, int(radius * 0.7))
        r_check_stddev = max(1, int(radius * 0.9))

        mask_brightness = np.zeros(image_gray.shape[:2], dtype=np.uint8)
        cv2.circle(mask_brightness, (x, y), r_check_brightness, 255, -1)
        roi_pixels_brightness = image_gray[mask_brightness == 255]

        if roi_pixels_brightness.size == 0:
            logger.debug(f"{context} ROI for brightness at ({x},{y}) R={r_check_brightness} is empty.")
            return False

        mean_brightness = np.mean(roi_pixels_brightness)

        if check_bright:
            if mean_brightness < brightness_threshold:
                logger.debug(f"{context} ROI at ({x},{y}) R={r_check_brightness} rejected: too dark ({mean_brightness:.2f} < {brightness_threshold})")
                return False
        else:
            if mean_brightness > brightness_threshold:
                logger.debug(f"{context} ROI at ({x},{y}) R={r_check_brightness} rejected: too bright ({mean_brightness:.2f} > {brightness_threshold})")
                return False

        mask_stddev = np.zeros(image_gray.shape[:2], dtype=np.uint8)
        cv2.circle(mask_stddev, (x, y), r_check_stddev, 255, -1)
        roi_pixels_stddev = image_gray[mask_stddev == 255]

        if roi_pixels_stddev.size < 10:
            logger.debug(f"{context} ROI for stddev at ({x},{y}) R={r_check_stddev} has too few pixels ({roi_pixels_stddev.size}). Skipping std dev check.")
            if roi_pixels_stddev.size == 0:
                return False
        else:
            std_dev_val = np.std(roi_pixels_stddev)
            if std_dev_val > max_std_dev:
                logger.debug(f"{context} ROI at ({x},{y}) R={r_check_stddev} rejected: std_dev too high ({std_dev_val:.2f} > {max_std_dev})")
                return False

        return True

    def detect_filter_papers(self, image: np.ndarray, dish: PetriDish) -> List[Colony]:
        logger.warning("detect_filter_papers 已被 _detect_substances_by_type 取代。")
        return self._detect_substances_by_type(image, dish, SubstanceType.FILTER_PAPER)

    def detect_holes(self, image: np.ndarray, dish: PetriDish) -> List[Colony]:
        logger.warning("detect_holes 已被 _detect_substances_by_type 取代。")
        return self._detect_substances_by_type(image, dish, SubstanceType.HOLE)

    def detect_inhibition_zones(self, image: np.ndarray) -> List[Dict]:
        """检测抑菌圈，基于 self.detected_substances 和 self.detection_mode"""
        logger.info(f"开始检测抑菌圈，模式: {self.detection_mode.name}, 物质类型: {self.substance_type.name}")

        if not self.detected_substances and self.detection_mode != DetectionMode.SINGLE_SUBSTANCE:
            logger.warning("没有检测到抑菌物质，无法检测抑菌圈。")
            return []

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        results = []
        substances_to_process = self.detected_substances

        for substance_obj in substances_to_process:
            x_sub, y_sub = substance_obj.center
            if substance_obj.radius <= 0:
                if hasattr(self, 'current_petri_dish_radius_px') and self.current_petri_dish_radius_px > 0:
                    search_roi_radius_px = int(self.current_petri_dish_radius_px * 0.8)
                else:
                    search_roi_radius_px = int(gray.shape[0] / 3)
                logger.info(f"物质点 {substance_obj.center} 半径小，使用默认搜索半径 {search_roi_radius_px}px")
            else:
                search_roi_radius_px = max(substance_obj.radius * 4, int(gray.shape[0] / 5))

            roi_abs_center_x, roi_abs_center_y = x_sub, y_sub
            roi_img, roi_x_offset, roi_y_offset = self._get_roi_with_offset(gray, roi_abs_center_x, roi_abs_center_y, search_roi_radius_px)

            if roi_img is None:
                logger.warning(f"无法获取物质点 {substance_obj.center} 周围的ROI。")
                continue

            processed_roi_for_zone = self.processor.preprocess(roi_img.copy())

            primary_zone_info = self._detect_primary_zone(
                processed_roi_for_zone,
                substance_obj,
                (roi_x_offset, roi_y_offset)
            )

            current_result = {
                'substance': substance_obj.to_dict() if hasattr(substance_obj, 'to_dict') else vars(substance_obj),
                'type': self.substance_type.name,
                'primary_zone': primary_zone_info
            }
            results.append(current_result)
            if not primary_zone_info:
                logger.info(f"物质点 {substance_obj.center} 未检测到主抑菌圈。")

        logger.info(f"抑菌圈检测完成，共处理 {len(substances_to_process)} 个物质点，得到 {len(results)} 个结果。")
        return results

    def _detect_primary_zone(self, roi_image: np.ndarray, substance: Colony, roi_offset: Tuple[int, int]) -> Optional[Dict]:
        """在物质周围 ROI 中检测主抑菌圈。

        方法:
        - 在 ROI 上构建多种分割（Otsu、反 Otsu、自适应小/大块）
        - 对每种分割找轮廓并计算轮廓特征（面积、圆度、距中心距离惩罚）
        - 对每个候选轮廓在灰度 ROI 上计算径向灰度剖面，评估是否存在环状暗带（谷值）
        - 将轮廓得分与径向剖面强度融合，选择得分最高的候选并返回其绝对坐标/半径/面积等信息
        """
        try:
            # roi_image 是处理过的灰度图（processor.preprocess 返回单通道）
            if len(roi_image.shape) > 2:
                roi_gray = cv2.cvtColor(roi_image, cv2.COLOR_BGR2GRAY)
            else:
                roi_gray = roi_image.copy()

            roi_h, roi_w = roi_gray.shape[:2]

            # 最小期望圈半径（像素）基于物质半径
            min_zone_radius_px = substance.radius * 1.1 if substance.radius > 0 else 10
            min_zone_area_px = np.pi * (min_zone_radius_px ** 2)

            # 生成多种分割
            segm_masks = {}
            _, th_otsu = cv2.threshold(roi_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            segm_masks['otsu'] = th_otsu
            segm_masks['inv_otsu'] = cv2.bitwise_not(th_otsu)
            segm_masks['adp_small'] = cv2.adaptiveThreshold(roi_gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                                           cv2.THRESH_BINARY_INV, 15, 5)
            segm_masks['adp_large'] = cv2.adaptiveThreshold(roi_gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                                           cv2.THRESH_BINARY_INV, 51, 9)

            def best_contour_from_mask(mask):
                cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                best = None
                best_score = 0.0
                for c in cnts:
                    area = cv2.contourArea(c)
                    if area < min_zone_area_px:
                        continue
                    peri = cv2.arcLength(c, True)
                    if peri <= 0:
                        continue
                    circularity = 4 * np.pi * area / (peri * peri + 1e-6)
                    (cx_c, cy_c), r_c = cv2.minEnclosingCircle(c)
                    # 中心惩罚：偏离物质中心越远越惩罚
                    substance_center_rel_x = substance.center[0] - roi_offset[0]
                    substance_center_rel_y = substance.center[1] - roi_offset[1]
                    dx = cx_c - (substance_center_rel_x)
                    dy = cy_c - (substance_center_rel_y)
                    dist = math.hypot(dx, dy)
                    center_penalty = max(0.0, 1.0 - (dist / (max(r_c, min_zone_radius_px) * 4 + 1e-6)))
                    score = circularity * (area ** 0.5) * center_penalty
                    if score > best_score:
                        best_score = score
                        best = {'contour': c, 'cx': cx_c, 'cy': cy_c, 'r': r_c, 'area': area, 'circularity': circularity, 'score': score}
                return best

            def radial_profile_strength(img_gray, cx_rel, cy_rel, r_min=3, r_max=None, nbins=36):
                if r_max is None:
                    r_max = int(min(img_gray.shape) / 2)
                radii = np.linspace(r_min, max(r_min + 1, r_max), nbins).astype(int)
                means = []
                h, w = img_gray.shape
                for ri in radii:
                    # annulus thickness 1: use circle perimeter sampling
                    mask = np.zeros_like(img_gray, dtype=np.uint8)
                    cv2.circle(mask, (int(cx_rel), int(cy_rel)), int(ri), 255, thickness=1)
                    vals = img_gray[mask == 255]
                    if vals.size == 0:
                        means.append(0.0)
                    else:
                        means.append(float(np.mean(vals)))
                arr = np.array(means)
                if arr.size < 5:
                    return 0.0
                min_idx = int(np.argmin(arr))
                left = np.mean(arr[max(0, min_idx - 3):min_idx]) if min_idx - 3 >= 0 else np.mean(arr[:min_idx + 1])
                right = np.mean(arr[min_idx + 1:min_idx + 4]) if min_idx + 4 <= arr.size else np.mean(arr[min_idx:])
                surround = np.mean([left, right]) if not (np.isnan(left) or np.isnan(right)) else np.mean(arr)
                if surround <= 0:
                    return 0.0
                valley_depth = max(0.0, surround - arr[min_idx])
                return valley_depth / (surround + 1e-6)

            best_overall = None
            best_overall_score = 0.0

            for name, mask in segm_masks.items():
                try:
                    candidate = best_contour_from_mask(mask)
                    if candidate is None:
                        continue
                    cx_c, cy_c, r_c = candidate['cx'], candidate['cy'], candidate['r']
                    rp = radial_profile_strength(roi_gray, cx_c, cy_c, r_min=3, r_max=int(max(roi_h, roi_w) / 2), nbins=36)
                    # increase radial-profile influence to favor ring-like patterns
                    combined = candidate['score'] * (1.0 + 6.0 * rp)
                    # slight favor for larger plausible radius
                    combined *= (1.0 + (r_c / (max(roi_h, roi_w) + 1e-6)))
                    if combined > best_overall_score:
                        best_overall_score = combined
                        best_overall = {'cx': candidate['cx'], 'cy': candidate['cy'], 'r': candidate['r'], 'area': candidate['area'], 'circularity': candidate['circularity'], 'seg': name}
                except Exception:
                    continue

            # Confidence threshold
            # lower confidence threshold to be more permissive for weak rings
            if best_overall is None or best_overall_score < 0.3:
                return None

            abs_center_x = int(best_overall['cx'] + roi_offset[0])
            abs_center_y = int(best_overall['cy'] + roi_offset[1])
            abs_radius = int(best_overall['r'])

            min_primary_ratio = getattr(CFG.inhibition_zone, 'primary_zone_min_ratio', None)
            if not isinstance(min_primary_ratio, (int, float)):
                min_primary_ratio = 0.0

            min_primary_radius_px = getattr(CFG.inhibition_zone, 'primary_zone_min_radius_px', None)
            if not isinstance(min_primary_radius_px, (int, float)):
                min_primary_radius_px = 0

            min_required_radius = max(
                int(((substance.radius or 0) * float(min_primary_ratio)) if min_primary_ratio else 0),
                int(min_primary_radius_px)
            )

            if abs_radius < max(1, min_required_radius):
                logger.info(
                    "Skipping primary zone candidate as bubble/noise: center=%s, radius=%dpx < min_required=%dpx",
                    (abs_center_x, abs_center_y), abs_radius, max(1, min_required_radius)
                )
                return None

            diameter_mm_val = 0.0
            if self.px_per_mm and self.px_per_mm > 0:
                diameter_mm_val = (abs_radius * 2) / self.px_per_mm

            result = {
                'center': (abs_center_x, abs_center_y),
                'radius': abs_radius,
                'diameter_mm': diameter_mm_val,
                'area_px': float(best_overall.get('area', 0.0)),
                'circularity': float(best_overall.get('circularity', 0.0)),
                'segmentation': best_overall.get('seg', 'unknown'),
                'score': float(best_overall_score)
            }
            logger.info(f"检测到主抑菌圈: 中心{result['center']}, 半径{result['radius']}px, 直径{result['diameter_mm']:.2f}mm (seg={result['segmentation']}, score={result['score']:.2f})")
            return result
        except Exception as ex:
            logger.exception(f"_detect_primary_zone 错误: {ex}")
            return None

    def _get_roi_with_offset(self, image: np.ndarray, center_x: int, center_y: int, radius: int) -> Tuple[Optional[np.ndarray], int, int]:
        h, w = image.shape[:2]
        x1 = max(0, center_x - radius)
        y1 = max(0, center_y - radius)
        x2 = min(w, center_x + radius)
        y2 = min(h, center_y + radius)

        if x2 <= x1 or y2 <= y1:
            return None, 0, 0

        return image[y1:y2, x1:x2], x1, y1

    def _get_roi(self, image: np.ndarray, x: int, y: int, radius: int) -> Optional[np.ndarray]:
        roi, _, _ = self._get_roi_with_offset(image, x, y, radius)
        return roi

    def _validate_dish_circle(self, image: np.ndarray, center: Tuple[int, int],
                            radius: int) -> bool:
        radius = max(1, radius)
        mask = np.zeros_like(image)
        cv2.circle(mask, center, radius, 255, 2)
        edge_pixels = cv2.bitwise_and(image, mask)

        if edge_pixels[edge_pixels > 0].size == 0:
            return False
        mean_value = np.mean(edge_pixels[edge_pixels > 0])
        return mean_value > 30

    def _create_circle_contour(self, center: Tuple[int, int],
                             radius: int) -> np.ndarray:
        radius = max(1, radius)
        angles = np.linspace(0, 2 * np.pi, 100)
        pts = np.array([
            [int(center[0] + radius * np.cos(theta)),
             int(center[1] + radius * np.sin(theta))]
            for theta in angles
        ], dtype=np.int32)
        return pts.reshape((-1, 1, 2))

    def process_image_pipeline(self, image: np.ndarray) -> Tuple[Optional[np.ndarray], List[Dict], Dict]:
        logger.info("开始完整的图像处理流程...")
        output_image = image.copy()
        all_dishes_results = []
        extra_info = {
            'petri_dishes_detected': 0,
            'substances_detected_total': 0,
            'inhibition_zones_detected_total': 0,
            'px_per_mm': None,
            'active_dish_details': []
        }

        dishes = self.detect_petri_dishes(image)
        if not dishes:
            logger.warning("未检测到培养皿。")
            return image, [], extra_info

        extra_info['petri_dishes_detected'] = len(dishes)
        extra_info['px_per_mm'] = self.px_per_mm

        for dish_idx, current_dish_obj in enumerate(dishes):
            logger.info(f"处理培养皿 #{dish_idx + 1} at {current_dish_obj.center} R={current_dish_obj.radius}")
            self.current_petri_dish_radius_px = current_dish_obj.radius

            cv2.circle(output_image, current_dish_obj.center, current_dish_obj.radius, (0, 255, 0), 2)
            cv2.putText(output_image, f"D{dish_idx+1}",
                       (current_dish_obj.center[0] - current_dish_obj.radius, current_dish_obj.center[1] - current_dish_obj.radius - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            mode, sub_type, substances_in_dish = self.analyze_dish_contents(image, current_dish_obj)

            dish_result_summary = {
                'dish_info': vars(current_dish_obj),
                'detection_mode': mode.name,
                'substance_type': sub_type.name,
                'substances_count': len(self.detected_substances),
                'zones_results': []
            }
            extra_info['substances_detected_total'] += len(self.detected_substances)

            if not self.detected_substances and mode == DetectionMode.SINGLE_SUBSTANCE:
                logger.info(f"培养皿 D{dish_idx+1}: 单一物质模式且无明确物质点，在培养皿中心创建虚拟搜索点。")
                default_substance_radius_mm = self.hole_diameter_mm / 2
                if self.px_per_mm and self.px_per_mm > 0:
                    default_substance_radius_px = int(default_substance_radius_mm * self.px_per_mm)
                else:
                    default_substance_radius_px = 10

                center_substance = Colony(
                    center=current_dish_obj.center,
                    radius=max(1, default_substance_radius_px),
                    contour=self._create_circle_contour(current_dish_obj.center, max(1, default_substance_radius_px))
                )
                self.detected_substances = [center_substance]
                dish_result_summary['substances_count'] = 1
                extra_info['substances_detected_total'] += 1
                logger.info(f"D{dish_idx+1}: 创建虚拟中心物质点: {center_substance.center}, R={center_substance.radius}px")

            for sub_idx, sub_obj in enumerate(self.detected_substances):
                color = (255, 100, 100) if self.substance_type == SubstanceType.FILTER_PAPER else (100, 100, 255)
                cv2.circle(output_image, sub_obj.center, sub_obj.radius, color, 2)
                cv2.circle(output_image, sub_obj.center, 2, (50, 50, 50), -1)
                cv2.putText(output_image, f"S{sub_idx+1}",
                           (sub_obj.center[0] + sub_obj.radius + 2, sub_obj.center[1]),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)

            current_dish_zone_results_list = self.detect_inhibition_zones(image)
            dish_result_summary['zones_results'] = current_dish_zone_results_list
            all_dishes_results.extend(current_dish_zone_results_list)

            num_zones_in_dish = sum(1 for zr in current_dish_zone_results_list if zr.get('primary_zone'))
            extra_info['inhibition_zones_detected_total'] += num_zones_in_dish

            for zone_res_dict in current_dish_zone_results_list:
                primary = zone_res_dict.get('primary_zone')
                if primary:
                    cv2.circle(output_image, primary['center'], primary['radius'], (50, 200, 200), 2)
                    cv2.putText(output_image, f"{primary['diameter_mm']:.1f}mm",
                               (primary['center'][0] + primary['radius'] + 5, primary['center'][1]),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (50, 200, 200), 2)

            extra_info['active_dish_details'].append(dish_result_summary)

        logger.info("完整流程处理完毕。")
        return output_image, all_dishes_results, extra_info
        if substance_type == SubstanceType.FILTER_PAPER:
            diameter_mm = self.filter_paper_diameter_mm
            processed_for_hough = self.processor.preprocess(masked_dish_gray)
            hough_param2_val = 28
            brightness_threshold_val = 120
            max_std_dev_val = 25.0 # Filter papers should be quite uniform
            check_roi_bright = True
            if self.px_per_mm and self.px_per_mm > 0:
                radius_factor_min = 0.85
                radius_factor_max = 1.15
        elif substance_type == SubstanceType.HOLE:
            diameter_mm = self.hole_diameter_mm
            inverted_gray = cv2.bitwise_not(masked_dish_gray)
            inverted_dish_roi = cv2.bitwise_and(inverted_gray, inverted_gray, mask=dish_mask)
            # 使用专用的孔洞预处理以增强透明边界
            processed_for_hough = self.processor.preprocess_for_hole(inverted_dish_roi)
            # For HOLEs, we are checking the inverted image for brightness (so it becomes a bright spot)
            # but the std_dev should be on the original image's ROI if we want to check darkness uniformity
            # Or, on the inverted image, it should also be uniform if the hole is uniformly dark.
            # Let's stick to validating the image that HoughCircles sees (inverted_dish_roi for HOLEs)
            hough_param1_val_for_hole = 40 # Lowered Canny high threshold for HOLEs
            # Lower param2 further to increase sensitivity for weak transparent edges
            hough_param2_val = 8 # was 12
            
            # These parameters are for the _validate_roi_brightness call on the ORIGINAL image
            brightness_threshold_val = 90  # For original image: holes should be darker than this
            max_std_dev_val = 35.0         # Holes in original image might have some variation, but not extreme like bubbles
            check_roi_bright = False       # Yes, check for dark in original image

            if self.px_per_mm and self.px_per_mm > 0:
                # 放宽搜索窗口以避免漏检
                radius_factor_min = 0.7
                radius_factor_max = 1.3
        else:
            return []

        # Calculate expected radius in pixels
        # If px_per_mm is not available or invalid, we can't use diameter_mm for radius estimation
        # In such cases, minRadius/maxRadius for HoughCircles will rely on broader estimates or fixed values.
        # However, the current logic for HoughCircles requires minRadius_px and maxRadius_px.
        # Let's ensure diameter_mm and px_per_mm are valid before calculating expected_radius_px.

        if diameter_mm > 0 and self.px_per_mm and self.px_per_mm > 0:
            expected_radius_px = int(diameter_mm * self.px_per_mm / 2)
            min_radius_px = max(5, int(expected_radius_px * radius_factor_min))
            max_radius_px = int(expected_radius_px * radius_factor_max)
            min_dist_hough = max(int(expected_radius_px * 1.8), 20)
            logger.info(f"进行 {substance_type.name} 检测: 预期半径 {expected_radius_px}px, 范围 [{min_radius_px}-{max_radius_px}]px, param2={hough_param2_val}")
        else:
            # Fallback if px_per_mm is not set (e.g. dish detection failed or diameter_mm is 0)
            # This case makes substance detection less reliable as it can't use physical size.
            # For now, we'll use broader, somewhat arbitrary pixel ranges if not calibrated.
            # This part might need to be disabled or handled differently if calibration is mandatory.
            logger.warning(f"px_per_mm ({self.px_per_mm}) 或物质直径 ({diameter_mm}mm) 无效，无法精确计算 {substance_type.name} 的预期像素半径。将使用较宽松的像素范围。")
            # Example fallback: (these values are quite arbitrary and should be tuned or rethought)
            if substance_type == SubstanceType.FILTER_PAPER:
                min_radius_px = 8  # e.g. for small filter papers in uncalibrated images
                max_radius_px = 40
            elif substance_type == SubstanceType.HOLE:
                min_radius_px = 5
                max_radius_px = 35
            else: # Should not happen due to earlier check
                return []
            min_dist_hough = max(int(min_radius_px * 2.5), 20) # Adjust minDist based on fallback min_radius
            logger.info(f"回退 {substance_type.name} 检测: 范围 [{min_radius_px}-{max_radius_px}]px, param2={hough_param2_val}")


        if min_radius_px <=0 or max_radius_px <=0 or min_radius_px >= max_radius_px : # 防止无效半径范围
             logger.warning(f"计算得到的最小半径({min_radius_px})或最大半径({max_radius_px})无效 for {substance_type.name}。跳过检测。")
             return []

        circles = cv2.HoughCircles(
            processed_for_hough,
            cv2.HOUGH_GRADIENT,
            dp=1.2,
            minDist=min_dist_hough,
            param1=hough_param1_val_for_hole if substance_type == SubstanceType.HOLE else 60, # Use specific param1 for HOLE
            param2=hough_param2_val,
            minRadius=min_radius_px,
            maxRadius=max_radius_px
        )

        detected_items = []
        if circles is not None:
            circles = np.uint16(np.around(circles))
            for x_u16, y_u16, r_u16 in circles[0, :]:
                # Convert to Python int or signed numpy int to avoid overflow in subtraction
                x, y, r = int(x_u16), int(y_u16), int(r_u16)
                
                # 验证必须在培养皿内部 (霍夫变换可能在边缘产生结果)
                # Ensure dish.center components are also treated as standard ints for safety
                dish_center_x, dish_center_y = int(dish.center[0]), int(dish.center[1])
                distance_to_center = np.sqrt((x - dish_center_x)**2 + (y - dish_center_y)**2)
                
                if distance_to_center + r > dish.radius:
                    # logger.debug(f"Substance at ({x},{y}) R={r} rejected: extends beyond dish radius {dish.radius}. Dist to center: {distance_to_center}")
                    continue

                # 过滤小的高光点（specular highlights）
                if self._is_specular_spot(masked_dish_gray, (x, y), r):
                    logger.debug(f"{validation_context} at ({x},{y}) R={r} 被判定为高光/小斑点，跳过。")
                    continue

                # 使用原始灰度图masked_dish_gray进行亮度 和 标准差 验证
                validation_context = f"{substance_type.name} candidate"
                # The brightness_threshold_val, max_std_dev_val, and check_roi_bright
                # were set specifically for the current substance_type earlier in this function.
                if self._validate_roi_brightness(
                    image_gray=masked_dish_gray,
                    center=(x,y),
                    radius=r,
                    brightness_threshold=brightness_threshold_val, # Use the specific threshold for this type
                    max_std_dev=max_std_dev_val,                   # Use the specific std_dev for this type
                    check_bright=check_roi_bright,                 # Use the specific check_bright for this type
                    context=validation_context
                ):
                    detected_items.append(Colony(
                        center=(int(x), int(y)),
                        radius=int(r),
                        contour=self._create_circle_contour((x, y), r),
                        substance_type=substance_type # Store the detected type
                    ))
            # 如果 HOUGH 没有检测到任何孔洞，尝试基于自适应阈值+轮廓的备选检测
            if substance_type == SubstanceType.HOLE and len(detected_items) == 0:
                logger.info("Hough 未检测到 HOLE，尝试自适应阈值+轮廓备选检测")
                try:
                    fallback = self._detect_holes_by_adaptive_threshold(masked_dish_gray, dish, min_radius_px, max_radius_px)
                    if fallback:
                        logger.info(f"自适应轮廓方法检测到 {len(fallback)} 个 HOLE 候选")
                        detected_items.extend(fallback)
                except Exception as e:
                    logger.exception(f"自适应阈值检测失败: {e}")

            logger.info(f"检测到 {len(detected_items)} 个 {substance_type.name}")
            return detected_items

        def _detect_holes_by_adaptive_threshold(self, image_gray: np.ndarray, dish: PetriDish,
                                               min_radius_px: int, max_radius_px: int) -> List[Colony]:
            """
            当 Hough 检测失败时的备选策略：使用自适应阈值或局部 Otsu + 轮廓检测来寻找透明孔洞（暗区）。
            返回 Colony 列表（可能为空）。
            """
            results: List[Colony] = []

            # 使用自适应阈值（对暗区使用 THRESH_BINARY_INV）
            try:
                # 降低分辨率再检验会更鲁棒，但这里直接用原图
                # blockSize must be odd and >1
                block_size = 31 if min(image_gray.shape[:2]) > 100 else 15
                adaptive = cv2.adaptiveThreshold(image_gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                                 cv2.THRESH_BINARY_INV, block_size, 8)

                # 形态学去噪
                kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
                opened = cv2.morphologyEx(adaptive, cv2.MORPH_OPEN, kernel, iterations=1)
                closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel, iterations=1)

                contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                for contour in contours:
                    area = cv2.contourArea(contour)
                    if area <= 0:
                        continue

                    perimeter = cv2.arcLength(contour, True)
                    if perimeter == 0:
                        continue

                    circularity = 4 * np.pi * area / (perimeter * perimeter)

                    # 过滤过小或过大的轮廓
                    (cx, cy), radius = cv2.minEnclosingCircle(contour)
                    cx_i, cy_i, radius_i = int(cx), int(cy), int(radius)

                    if radius_i < min_radius_px or radius_i > max_radius_px:
                        continue

                    # 面积门限：至少比一个较小阈值大
                    if area < np.pi * (max(3, min_radius_px*0.5) ** 2):
                        continue

                    # 圆度放宽到 0.35 允许透明边界不太规则
                    if circularity < 0.35:
                        continue

                    # 检查是否高光点
                    if self._is_specular_spot(image_gray, (cx_i, cy_i), radius_i):
                        continue

                    # 验证亮度（孔洞应为暗区）
                    if not self._validate_roi_brightness(image_gray, (cx_i, cy_i), radius_i,
                                                         brightness_threshold=120, max_std_dev=60,
                                                         check_bright=False, context='adaptive_hole'):
                        continue

                    # 验证该候选在培养皿内部
                    distance_to_center = np.sqrt((cx - dish.center[0])**2 + (cy - dish.center[1])**2)
                    if distance_to_center + radius > dish.radius:
                        continue

                    results.append(Colony(
                        center=(cx_i, cy_i),
                        radius=radius_i,
                        contour=contour,
                        substance_type=SubstanceType.HOLE
                    ))

            except Exception as ex:
                logger.exception(f"adaptive hole detection error: {ex}")

            return results

    _process_image_pipeline_impl = process_image_pipeline

    def _is_specular_spot(self, image_gray: np.ndarray, center: Tuple[int, int], radius: int) -> bool:
        """
        简单判断一个候选是否为小的高光点或气泡：
        - 如果候选区域非常小且最大亮度远高于局部中值，则视为高光
        - 以像素差和面积为判定标准
        """
        x, y = center
        h, w = image_gray.shape[:2]
        r_check = max(1, int(radius))
        x1 = max(0, x - r_check)
        y1 = max(0, y - r_check)
        x2 = min(w, x + r_check)
        y2 = min(h, y + r_check)

        roi = image_gray[y1:y2, x1:x2]
        if roi.size == 0:
            return False

        max_val = np.max(roi)
        median_val = np.median(roi)
        area_px = roi.shape[0] * roi.shape[1]

        # 若区域面积很小且最大值远高于中位数，则判为高光
        if area_px <= 50 and (max_val - median_val) > 100:
            return True

        return False

    def _validate_roi_brightness(self, image_gray: np.ndarray, center: Tuple[int, int], radius: int,
                                 brightness_threshold: float, max_std_dev: float,
                                 check_bright: bool = True, context: str = "") -> bool:
        """
        验证ROI区域的平均亮度是否符合预期，并且灰度标准差是否在允许范围内。
        check_bright=True: 检查是否足够亮 (如滤纸片)
        check_bright=False: 检查是否足够暗 (如孔洞在原图中)
        """
        x, y = center
        # 取内部区域进行判断，避免边缘影响
        r_check_brightness = max(1, int(radius * 0.7))
        r_check_stddev = max(1, int(radius * 0.9))

        # --- Brightness Check ---
        mask_brightness = np.zeros(image_gray.shape[:2], dtype=np.uint8)
        cv2.circle(mask_brightness, (x,y), r_check_brightness, 255, -1)
        roi_pixels_brightness = image_gray[mask_brightness == 255]

        if roi_pixels_brightness.size == 0:
            logger.debug(f"{context} ROI for brightness at ({x},{y}) R={r_check_brightness} is empty.")
            return False
        
        mean_brightness = np.mean(roi_pixels_brightness)

        if check_bright:
            if mean_brightness < brightness_threshold:
                logger.debug(f"{context} ROI at ({x},{y}) R={r_check_brightness} rejected: too dark ({mean_brightness:.2f} < {brightness_threshold})")
                return False
        else: # check_dark
            if mean_brightness > brightness_threshold:
                logger.debug(f"{context} ROI at ({x},{y}) R={r_check_brightness} rejected: too bright ({mean_brightness:.2f} > {brightness_threshold})")
                return False
        
        # --- Standard Deviation Check ---
        mask_stddev = np.zeros(image_gray.shape[:2], dtype=np.uint8)
        cv2.circle(mask_stddev, (x,y), r_check_stddev, 255, -1)
        roi_pixels_stddev = image_gray[mask_stddev == 255]

        if roi_pixels_stddev.size < 10:
            logger.debug(f"{context} ROI for stddev at ({x},{y}) R={r_check_stddev} has too few pixels ({roi_pixels_stddev.size}). Skipping std dev check.")
            if roi_pixels_stddev.size == 0: return False
        else:
            std_dev_val = np.std(roi_pixels_stddev)
            # logger.debug(f"{context} ROI at ({x},{y}) R={r_check_stddev}: StdDev {std_dev_val:.2f}")
            if std_dev_val > max_std_dev:
                logger.debug(f"{context} ROI at ({x},{y}) R={r_check_stddev} rejected: std_dev too high ({std_dev_val:.2f} > {max_std_dev})")
                return False
        
        # logger.debug(f"{context} ROI at ({x},{y}) R(b)={r_check_brightness},R(s)={r_check_stddev} accepted: brightness {mean_brightness:.2f}, std_dev {std_dev_val if roi_pixels_stddev.size >=10 else 'N/A'}")
        return True

    def detect_filter_papers(self, image: np.ndarray, dish: PetriDish) -> List[Colony]:
        logger.warning("detect_filter_papers 已被 _detect_substances_by_type 取代。")
        return self._detect_substances_by_type(image, dish, SubstanceType.FILTER_PAPER)

    def detect_holes(self, image: np.ndarray, dish: PetriDish) -> List[Colony]:
        logger.warning("detect_holes 已被 _detect_substances_by_type 取代。")
        return self._detect_substances_by_type(image, dish, SubstanceType.HOLE)

    def detect_inhibition_zones(self, image: np.ndarray) -> List[Dict]:
        """检测抑菌圈，基于 self.detected_substances 和 self.detection_mode"""
        logger.info(f"开始检测抑菌圈，模式: {self.detection_mode.name}, 物质类型: {self.substance_type.name}")

        if not self.detected_substances and self.detection_mode != DetectionMode.SINGLE_SUBSTANCE:
            logger.warning("没有检测到抑菌物质，无法检测抑菌圈。")
            return []
        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        results = []
        substances_to_process = self.detected_substances

        # 如果是单一物质模式且列表为空，则在当前活动培养皿中心创建虚拟搜索点
        # 这需要在调用此函数前，由 process_image_pipeline 确保 self.detected_substances 被正确填充
        # (已在 process_image_pipeline 中处理)

        for substance_obj in substances_to_process:
            x_sub, y_sub = substance_obj.center
            # 抑菌圈搜索半径：可以基于物质半径的倍数，或培养皿半径的一部分
            # 确保 substance_obj.radius > 0
            if substance_obj.radius <= 0: # 比如虚拟中心点可能半径为0或很小
                 # 使用培养皿半径的比如1/2作为搜索半径
                if hasattr(self, 'current_petri_dish_radius_px') and self.current_petri_dish_radius_px > 0:
                     search_roi_radius_px = int(self.current_petri_dish_radius_px * 0.8) # 搜索范围大一些
                else: # Fallback
                    search_roi_radius_px = int(gray.shape[0] / 3) # 图像高度的1/3
                logger.info(f"物质点 {substance_obj.center} 半径小，使用默认搜索半径 {search_roi_radius_px}px")
            else:
                search_roi_radius_px = max(substance_obj.radius * 4, int(gray.shape[0] / 5) ) # 至少是物质半径4倍，或图像的1/5

            # 获取ROI及其在原图的偏移
            roi_abs_center_x, roi_abs_center_y = x_sub, y_sub
            roi_img, roi_x_offset, roi_y_offset = self._get_roi_with_offset(gray, roi_abs_center_x, roi_abs_center_y, search_roi_radius_px)

            if roi_img is None:
                logger.warning(f"无法获取物质点 {substance_obj.center} 周围的ROI。")
                continue
            
            # 对ROI进行预处理，以增强抑菌圈的特征
            # processed_roi_for_zone = self.processor.enhance_contrast(roi_img.copy()) # 尝试对比度增强
            # 或者使用更通用的预处理
            processed_roi_for_zone = self.processor.preprocess(roi_img.copy())


            primary_zone_info = self._detect_primary_zone(
                processed_roi_for_zone,
                substance_obj, # 传递原始物质对象
                (roi_x_offset, roi_y_offset) # 传递ROI在原图的左上角坐标
            )

            current_result = {
                'substance': substance_obj.to_dict() if hasattr(substance_obj, 'to_dict') else vars(substance_obj), # Convert Colony to dict
                'type': self.substance_type.name,
                'primary_zone': primary_zone_info
            }
            results.append(current_result)
            if not primary_zone_info:
                 logger.info(f"物质点 {substance_obj.center} 未检测到主抑菌圈。")
        
        logger.info(f"抑菌圈检测完成，共处理 {len(substances_to_process)} 个物质点，得到 {len(results)} 个结果。")
        return results

    def _detect_primary_zone(self, roi_image: np.ndarray, substance: Colony, roi_offset: Tuple[int, int]) -> Optional[Dict]:
        """
        检测主抑菌圈 (在ROI内操作)
        substance: 是滤纸片或孔洞对象
        roi_offset: 是该ROI在原图中的左上角坐标 (x_offset, y_offset)
        返回的抑菌圈坐标是相对于原图的。
        """
        # 假设抑菌圈是比周围菌落更亮的区域
        # 使用OTSU阈值分割亮区
        _, binary_roi = cv2.threshold(roi_image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        # 如果抑菌圈是暗区，则需要 cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU 或反转 binary_roi

        # For debugging, you can add:
        # cv2.imshow(f"Binary ROI for substance {substance.center}", binary_roi)
        # cv2.waitKey(1)


        kernel_size = 3 # Reduced kernel size for morphology
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
        binary_roi = cv2.morphologyEx(binary_roi, cv2.MORPH_OPEN, kernel, iterations=1)
        # binary_roi = cv2.morphologyEx(binary_roi, cv2.MORPH_CLOSE, kernel, iterations=2) # Reduced iterations or remove one
        binary_roi = cv2.morphologyEx(binary_roi, cv2.MORPH_CLOSE, kernel, iterations=1)


        # For debugging, you can add:
        # temp_roi_color = cv2.cvtColor(binary_roi, cv2.COLOR_GRAY2BGR)
        contours, _ = cv2.findContours(binary_roi, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        # cv2.drawContours(temp_roi_color, contours, -1, (0,255,0), 1)
        # cv2.imshow(f"Contours on Binary ROI for {substance.center}", temp_roi_color)
        # cv2.waitKey(1)

        best_zone_abs = None
        max_score = -1 # Initialize with a value that any valid score can beat

        # 抑菌圈的最小预期半径：至少比物质半径大一点
        min_zone_radius_px = substance.radius * 1.1 if substance.radius > 0 else 10 # 最小10px
        min_zone_area_px = np.pi * (min_zone_radius_px ** 2)


        for contour in contours:
            area = cv2.contourArea(contour)
            if area < min_zone_area_px:
                continue

            perimeter = cv2.arcLength(contour, True)
            if perimeter == 0: continue
            circularity = 4 * np.pi * area / (perimeter * perimeter) if perimeter > 0 else 0

            if circularity > 0.5: # 放宽圆度要求
                (x_rel, y_rel), radius_rel = cv2.minEnclosingCircle(contour)

                if radius_rel < min_zone_radius_px : # 确保抑菌圈半径足够大
                    continue

                # 确保抑菌圈中心大致在物质中心附近 (在ROI坐标系下)
                # substance的中心是绝对坐标，需要转换到ROI的相对坐标
                substance_center_rel_x = substance.center[0] - roi_offset[0]
                substance_center_rel_y = substance.center[1] - roi_offset[1]
                
                # 计算检测到的圆心与物质中心的距离
                dist_sq = (x_rel - substance_center_rel_x)**2 + (y_rel - substance_center_rel_y)**2
                # 允许的最大偏移量，例如物质半径的2倍
                max_offset_allowed = (substance.radius * 2)**2 if substance.radius > 0 else (20*2)**2 # 默认20px半径的2倍

                if dist_sq > max_offset_allowed:
                    # logger.debug(f"抑菌圈候选区 ({x_rel:.0f},{y_rel:.0f}) R={radius_rel:.0f} 偏离物质中心太远，跳过。")
                    continue
                
                # 评分可以综合面积和圆度，以及与物质中心的接近程度（距离越小越好）
                # score = circularity * area / (1 + np.sqrt(dist_sq)) # 距离越小，分母越小，分数越高
                score = circularity * area # 简化评分

                if score > max_score:
                    max_score = score
                    abs_center_x = int(x_rel + roi_offset[0])
                    abs_center_y = int(y_rel + roi_offset[1])
                    abs_radius = int(radius_rel)

                    diameter_mm_val = 0.0
                    if self.px_per_mm and self.px_per_mm > 0:
                        diameter_mm_val = (abs_radius * 2) / self.px_per_mm
                    else:
                        logger.warning("px_per_mm 未标定或为0，无法计算抑菌圈直径(mm)")

                    best_zone_abs = {
                        'center': (abs_center_x, abs_center_y),
                        'radius': abs_radius,
                        'diameter_mm': diameter_mm_val,
                        'area_px': area,
                        'circularity': circularity
                    }
        
        if best_zone_abs:
            logger.info(f"检测到主抑菌圈: 中心{best_zone_abs['center']}, 半径{best_zone_abs['radius']}px, 直径{best_zone_abs['diameter_mm']:.2f}mm")
        return best_zone_abs

    def _get_roi_with_offset(self, image: np.ndarray, center_x: int, center_y: int, radius: int) -> Tuple[Optional[np.ndarray], int, int]:
        """获取感兴趣区域 (ROI) 及其在原图中的左上角偏移量"""
        h, w = image.shape[:2]
        x1 = max(0, center_x - radius)
        y1 = max(0, center_y - radius)
        x2 = min(w, center_x + radius)
        y2 = min(h, center_y + radius)

        if x2 <= x1 or y2 <= y1:
            return None, 0, 0
        
        return image[y1:y2, x1:x2], x1, y1

    def _get_roi(self, image: np.ndarray, x: int, y: int, radius: int) -> Optional[np.ndarray]:
        """获取感兴趣区域 (兼容旧用法，但不推荐，请用 _get_roi_with_offset)"""
        roi, _, _ = self._get_roi_with_offset(image, x, y, radius)
        return roi
        
    def _validate_dish_circle(self, image: np.ndarray, center: Tuple[int, int],
                            radius: int) -> bool:
        """验证培养皿圆的有效性"""
        # 确保半径至少为1
        radius = max(1, radius)
        mask = np.zeros_like(image)
        cv2.circle(mask, center, radius, 255, 2) # 检查边缘
        edge_pixels = cv2.bitwise_and(image, mask)
        
        if edge_pixels[edge_pixels > 0].size == 0: return False # 没有边缘像素
        mean_value = np.mean(edge_pixels[edge_pixels > 0])
        # logger.debug(f"Dish validation: center={center}, R={radius}, edge_mean={mean_value}")
        return mean_value > 30 # 培养皿边缘的平均像素值阈值 (可调)

    # _validate_paper_circle is replaced by _validate_roi_brightness

    def _create_circle_contour(self, center: Tuple[int, int],
                             radius: int) -> np.ndarray:
        """创建圆形轮廓点集"""
        # 确保半径至少为1
        radius = max(1, radius)
        angles = np.linspace(0, 2*np.pi, 100)
        pts = np.array([
            [int(center[0] + radius*np.cos(theta)),
             int(center[1] + radius*np.sin(theta))]
            for theta in angles
        ], dtype=np.int32)
        return pts.reshape((-1, 1, 2))

    def process_image_pipeline(self, image: np.ndarray) -> Tuple[Optional[np.ndarray], List[Dict], Dict]:
        return self._process_image_pipeline_impl(image)

