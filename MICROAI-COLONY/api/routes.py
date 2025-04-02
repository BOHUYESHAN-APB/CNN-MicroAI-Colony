"""
API路由模块 - 提供RESTful接口
"""
from flask import Blueprint, request, jsonify, current_app, send_file
import os
import cv2
import numpy as np
from werkzeug.utils import secure_filename
from core.model_loader import load_model, ColonyAnalyzer
from core.image_preprocessor import ImagePreprocessor
from io import BytesIO

api_bp = Blueprint('api', __name__)

@api_bp.route('/analyze', methods=['POST']) 
def analyze_image():
    """单张图片分析"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # 确保上传目录存在
        os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        
        try:
            file.save(filepath)
            
            # 获取参数
            model_type = request.form.get('model_type', 'balanced')
            preprocess_methods = request.form.getlist('preprocess_methods') or None
            
            # 获取预处理参数
            preprocess_params = {}
            if 'gaussian_blur_kernel_size' in request.form:
                preprocess_params['gaussian_blur'] = {
                    'kernel_size': int(request.form['gaussian_blur_kernel_size'])
                }
            if 'watershed_threshold' in request.form:
                preprocess_params['watershed'] = {
                    'marker_threshold': float(request.form['watershed_threshold'])
                }
            
            model = load_model(model_type)
            analyzer = ColonyAnalyzer(model)
            result = analyzer.analyze(filepath, preprocess_methods, preprocess_params)
            
            # 转换NumPy数组为可JSON序列化的Python类型
            if 'scores' in result:
                result['scores'] = [float(score) for score in result['scores']]
            if 'boxes' in result:
                result['boxes'] = [box.tolist() if hasattr(box, 'tolist') else box for box in result['boxes']]
            
            # 添加图片尺寸信息供前端使用
            img = cv2.imread(filepath)
            if img is not None:
                result['image_width'] = int(img.shape[1])
                result['image_height'] = int(img.shape[0])
            
            return jsonify(result)
            
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f'分析失败: {str(e)}'
            }), 500
    
    return jsonify({'error': 'Invalid file type'}), 400

@api_bp.route('/analyze_batch', methods=['POST'])
def analyze_batch():
    """批量分析图片"""
    if 'files[]' not in request.files:
        return jsonify({'error': 'No files part'}), 400
        
    files = request.files.getlist('files[]')
    if not files:
        return jsonify({'error': 'No selected files'}), 400
    
    results = []
    model_type = request.form.get('model_type', 'balanced')
    preprocess_methods = request.form.getlist('preprocess_methods') or None
    
    # 获取预处理参数
    preprocess_params = {}
    if 'gaussian_blur_kernel_size' in request.form:
        preprocess_params['gaussian_blur'] = {
            'kernel_size': int(request.form['gaussian_blur_kernel_size'])
        }
    if 'watershed_threshold' in request.form:
        preprocess_params['watershed'] = {
            'marker_threshold': float(request.form['watershed_threshold'])
        }
    
    model = load_model(model_type)
    analyzer = ColonyAnalyzer(model)
    
    # 确保上传目录存在
    os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            try:
                # 分析并生成带标注的图片
                result = analyzer.analyze(filepath, preprocess_methods, preprocess_params)
                result['filename'] = filename
                
                # 生成带标注的图片
                img = cv2.imread(filepath)
                if result['status'] == 'success':
                    for box in result['boxes']:
                        x1, y1, x2, y2 = map(int, box)
                        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 2)
                
                # 保存标注图片
                annotated_filename = f"annotated_{filename}"
                annotated_path = os.path.join(current_app.config['UPLOAD_FOLDER'], annotated_filename)
                cv2.imwrite(annotated_path, img)
                result['annotated_image'] = annotated_filename
                
                # 转换NumPy数组
                if 'boxes' in result:
                    result['boxes'] = [box.tolist() if hasattr(box, 'tolist') else box for box in result['boxes']]
                
                results.append(result)
                
            except Exception as e:
                results.append({
                    'filename': filename,
                    'status': 'error',
                    'message': str(e)
                })
    
    return jsonify(results)

@api_bp.route('/annotated_image', methods=['POST'])
def get_annotated_image():
    """生成带标注的图片"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if not file or file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    try:
        # 读取图片
        img_bytes = file.read()
        img_array = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        
        # 获取分析结果
        model_type = request.form.get('model_type', 'balanced')
        model = load_model(model_type)
        analyzer = ColonyAnalyzer(model)
        
        # 临时保存图片用于分析
        temp_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'temp.jpg')
        cv2.imwrite(temp_path, img)
        result = analyzer.analyze(temp_path)
        
        # 绘制标注
        if result['status'] == 'success':
            for box in result['boxes']:
                x1, y1, x2, y2 = map(int, box)
                cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 2)
        
        # 返回图片
        _, img_encoded = cv2.imencode('.jpg', img)
        img_bytes = BytesIO(img_encoded.tobytes())
        
        return send_file(img_bytes, mimetype='image/jpeg')
        
    except Exception as e:
        return jsonify({
            'status': 'error', 
            'message': f'生成标注图片失败: {str(e)}'
        }), 500

def allowed_file(filename):
    """检查文件扩展名是否合法"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']
