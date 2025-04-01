"""
菌落分析系统主应用 - Flask版本
MicroAI Colony Analyzer (Flask)
"""
from flask import Flask, render_template, send_from_directory
import os

# 初始化应用
app = Flask(__name__)
app.config.from_pyfile('config.py')

# 配置上传文件夹路由
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# 注册蓝图
from api.routes import api_bp
app.register_blueprint(api_bp, url_prefix='/api')

@app.route('/')
def index():
    """主界面"""
    return render_template('index.html')

if __name__ == '__main__':
    from werkzeug.middleware.proxy_fix import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app)
    app.config['PROPAGATE_EXCEPTIONS'] = True
    app.run(debug=True, host='0.0.0.0', port=5000)
