document.addEventListener('DOMContentLoaded', function() {
    // 初始化元素引用
    const themeSwitch = document.getElementById('themeSwitch');
    const fileInput = document.getElementById('file-input');
    const dropArea = document.getElementById('drop-area');
    const batchFileInput = document.getElementById('batch-file-input');
    const batchDropArea = document.getElementById('batch-drop-area');
    const imageCanvas = document.getElementById('imageCanvas');
    const ctx = imageCanvas.getContext('2d');
    const analyzeBtn = document.getElementById('analyze-btn');
    const batchAnalyzeBtn = document.getElementById('batch-analyze-btn');
    const modelType = document.getElementById('model-type');
    const confidenceThreshold = document.getElementById('confidenceThreshold');
    const thresholdValue = document.getElementById('thresholdValue');
    const showBoxes = document.getElementById('showBoxes');
    const showScores = document.getElementById('showScores');
    const showCenters = document.getElementById('showCenters');
    const exportImageBtn = document.getElementById('exportImageBtn');
    const exportDataBtn = document.getElementById('exportDataBtn');
    const exportBatchBtn = document.getElementById('exportBatchBtn');
    const resultDiv = document.getElementById('result');
    const grayscaleCheck = document.getElementById('grayscaleCheck');
    const histEqualCheck = document.getElementById('histEqualCheck');
    const blurCheck = document.getElementById('blurCheck');
    
    // 当前分析结果和原始图片
    let currentImage = null;
    let currentResults = null;
    let batchResults = [];

    // 1. 主题切换功能
    themeSwitch.addEventListener('change', function() {
        const newTheme = this.checked ? 'dark' : 'light';
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        drawAnnotations();
    });

    // 初始化主题
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    themeSwitch.checked = savedTheme === 'dark';

    // 2. 图片上传处理
    function handleInteraction(file) {
        if (!file.type.match('image.*')) {
            alert('请选择图片文件');
            return false;
        }
        return true;
    }

    // 3. 单图上传处理
    function handleFile(file) {
        if (!handleInteraction(file)) return;

        const reader = new FileReader();
        reader.onload = function(e) {
            currentImage = new Image();
            currentImage.onload = function() {
                const container = imageCanvas.parentElement;
                const ratio = currentImage.width / currentImage.height;
                imageCanvas.width = container.clientWidth;
                imageCanvas.height = imageCanvas.width / ratio;
                
                ctx.drawImage(currentImage, 0, 0, imageCanvas.width, imageCanvas.height);
                dropArea.innerHTML = `<p>已选择: ${file.name}</p>`;
            };
            currentImage.src = e.target.result;
        };
        reader.readAsDataURL(file);
    }

    // 4. 获取选择的预处理方法
    function getPreprocessMethods(formData) {
        const methods = [];
        if (grayscaleCheck.checked) methods.push('grayscale');
        if (histEqualCheck.checked) methods.push('hist_equal');
        if (blurCheck.checked) {
            methods.push('gaussian_blur');
            formData.append('gaussian_blur_kernel_size', document.getElementById('blurSize').value);
        }
        if (document.getElementById('edgeCheck').checked) methods.push('edge_detect');
        if (document.getElementById('watershedCheck').checked) {
            methods.push('watershed');
            formData.append('watershed_threshold', document.getElementById('watershedThreshold').value);
        }
        return methods.length > 0 ? methods : null;
    }

    // 5. 单图分析
    analyzeBtn.addEventListener('click', async function() {
        if (!currentImage) {
            alert('请先选择图片');
            return;
        }

        analyzeBtn.disabled = true;
        analyzeBtn.textContent = '分析中...';

        try {
            const formData = new FormData();
            formData.append('file', fileInput.files[0]);
            formData.append('model_type', modelType.value);
            
            // 添加预处理参数
            const methods = getPreprocessMethods(formData);
            if (methods) {
                methods.forEach(method => {
                    formData.append('preprocess_methods', method);
                });
            }

            const response = await fetch('/api/analyze', {
                method: 'POST',
                body: formData
            });

            currentResults = await response.json();

            if (currentResults.status === 'success') {
                showResults(currentResults);
                drawAnnotations();
            } else {
                resultDiv.innerHTML = `<div class="alert alert-danger">分析失败: ${currentResults.message || '未知错误'}</div>`;
            }
        } catch (error) {
            resultDiv.innerHTML = `<div class="alert alert-danger">请求失败: ${error.message}</div>`;
        } finally {
            analyzeBtn.disabled = false;
            analyzeBtn.textContent = '单图分析';
        }
    });

    // 6. 批量分析
    batchAnalyzeBtn.addEventListener('click', async function() {
        const files = batchFileInput.files;
        if (files.length === 0) {
            alert('请先选择图片');
            return;
        }

        batchAnalyzeBtn.disabled = true;
        batchAnalyzeBtn.textContent = '批量分析中...';

        try {
            const formData = new FormData();
            Array.from(files).forEach(file => {
                formData.append('files[]', file);
            });
            formData.append('model_type', modelType.value);
            
            // 添加预处理参数
            const methods = getPreprocessMethods(formData);
            if (methods) {
                methods.forEach(method => {
                    formData.append('preprocess_methods', method);
                });
            }

            const response = await fetch('/api/analyze_batch', {
                method: 'POST',
                body: formData
            });
            
            batchResults = await response.json();
            updateBatchResultsUI(batchResults);
            
        } catch (error) {
            document.getElementById('batch-results').innerHTML = 
                `<div class="alert alert-danger">请求失败: ${error.message}</div>`;
        } finally {
            batchAnalyzeBtn.disabled = false;
            batchAnalyzeBtn.textContent = '批量分析';
        }
    });

    // 7. 更新批量结果UI
    function updateBatchResultsUI(results) {
        const batchResultsDiv = document.getElementById('batch-results');
        let html = '';
        
        results.forEach(result => {
            html += `
                <div class="result-item">
                    <strong>${result.filename}</strong>
                    <div>状态: ${result.status === 'success' ? '成功' : '失败'}</div>
                    ${result.status === 'success' ? 
                        `<div>菌落数量: ${result.count}</div>
                         <div>平均大小: ${result.sizes?.length ? 
                            (result.sizes.reduce((a,b) => a + b, 0) / result.sizes.length).toFixed(2) : 0}px</div>` : 
                        `<div class="text-danger">错误: ${result.message}</div>`}
                </div>
            `;
        });
        
        batchResultsDiv.innerHTML = html;
    }

    // 8. 单图结果显示
    function showResults(data) {
        const avgSize = data.sizes?.length ? 
            (data.sizes.reduce((a,b) => a + b, 0) / data.sizes.length).toFixed(2) : 0;
        
        resultDiv.innerHTML = `
            <div class="result-summary">
                <h5>分析结果摘要</h5>
                <p>菌落数量: <strong>${data.count}</strong></p>
                <p>平均大小: <strong>${avgSize}px²</strong></p>
            </div>
        `;
    }

    // 9. 绘制标注
    function drawAnnotations() {
        if (!currentImage || !currentResults || currentResults.status !== 'success') return;

        ctx.clearRect(0, 0, imageCanvas.width, imageCanvas.height);
        ctx.drawImage(currentImage, 0, 0, imageCanvas.width, imageCanvas.height);

        const imgWidth = currentResults.image_width || currentImage.width;
        const imgHeight = currentResults.image_height || currentImage.height;
        
        const scaleX = imageCanvas.width / imgWidth;
        const scaleY = imageCanvas.height / imgHeight;

        if (showBoxes.checked) {
            ctx.strokeStyle = '#FF0000';
            ctx.lineWidth = 2;
            ctx.font = '12px Arial';
            ctx.fillStyle = showScores.checked ? 'rgba(255,255,255,0.7)' : 'rgba(255,0,0,0.3)';

            currentResults.boxes.forEach((box, i) => {
                const [x1, y1, x2, y2] = box;
                const score = currentResults.scores[i];
                
                ctx.beginPath();
                ctx.rect(x1 * scaleX, y1 * scaleY, (x2 - x1) * scaleX, (y2 - y1) * scaleY);
                ctx.stroke();
                
                if (showScores.checked) {
                    ctx.fillRect(x1 * scaleX, y1 * scaleY - 20, 60, 20);
                }
                
                if (showScores.checked) {
                    ctx.fillStyle = '#000000';
                    ctx.fillText(`${(score * 100).toFixed(1)}%`, x1 * scaleX + 5, y1 * scaleY - 5);
                    ctx.fillStyle = 'rgba(255,255,255,0.7)';
                }
                
                if (showCenters.checked) {
                    const centerX = (x1 + x2) / 2 * scaleX;
                    const centerY = (y1 + y2) / 2 * scaleY;
                    
                    ctx.beginPath();
                    ctx.arc(centerX, centerY, 3, 0, Math.PI * 2);
                    ctx.fillStyle = '#00FF00';
                    ctx.fill();
                }
            });
        }
    }

    // 10. 显示设置变化时重绘
    [showBoxes, showScores, showCenters].forEach(control => {
        control.addEventListener('change', drawAnnotations);
    });

    // 11. 置信度阈值显示
    confidenceThreshold.addEventListener('input', function() {
        thresholdValue.textContent = this.value;
    });

    // 12. 导出功能
    exportImageBtn.addEventListener('click', function() {
        if (!currentImage) {
            alert('没有可导出的图像');
            return;
        }
        
        const link = document.createElement('a');
        link.download = 'colony-analysis.png';
        link.href = imageCanvas.toDataURL('image/png');
        link.click();
    });

    exportDataBtn.addEventListener('click', function() {
        if (!currentResults) {
            alert('没有可导出的数据');
            return;
        }
        
        let csvContent = "data:text/csv;charset=utf-8,";
        csvContent += "左上X,左上Y,右下X,右下Y,置信度,面积\n";
        
        currentResults.boxes.forEach((box, i) => {
            const width = box[2] - box[0];
            const height = box[3] - box[1];
            const area = width * height;
            csvContent += `${box.join(',')},${currentResults.scores[i]},${area}\n`;
        });
        
        const encodedUri = encodeURI(csvContent);
        const link = document.createElement('a');
        link.setAttribute('href', encodedUri);
        link.setAttribute('download', 'colony_data.csv');
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    });

    // 13. 批量结果导出
    exportBatchBtn.addEventListener('click', function() {
        if (batchResults.length === 0) {
            alert('没有可导出的批量结果');
            return;
        }
        
        let csvContent = "data:text/csv;charset=utf-8,";
        csvContent += "文件名,状态,菌落数量,平均大小,错误信息\n";
        
        batchResults.forEach(result => {
            const avgSize = result.sizes?.length ? 
                (result.sizes.reduce((a,b) => a + b, 0) / result.sizes.length).toFixed(2) : 0;
            
            csvContent += `"${result.filename}",${result.status},${result.count || ''},${avgSize},"${result.message || ''}"\n`;
        });
        
        const encodedUri = encodeURI(csvContent);
        const link = document.createElement('a');
        link.setAttribute('href', encodedUri);
        link.setAttribute('download', 'batch_results.csv');
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    });

    // 14. 拖放和点击上传处理
    dropArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropArea.style.borderColor = 'var(--primary-color)';
    });

    dropArea.addEventListener('dragleave', () => {
        dropArea.style.borderColor = 'var(--border-color)';
    });

    dropArea.addEventListener('drop', (e) => {
        e.preventDefault();
        dropArea.style.borderColor = 'var(--border-color)';
        if (e.dataTransfer.files.length) {
            handleFile(e.dataTransfer.files[0]);
        }
    });

        dropArea.addEventListener('click', (e) => {
            console.log('点击上传区域', e);
            console.log('文件输入元素:', fileInput);
            fileInput.click();
        });
        fileInput.addEventListener('change', () => {
            console.log('File selected:', fileInput.files); // 添加调试日志
            if (fileInput.files.length) {
                handleFile(fileInput.files[0]);
            } else {
                console.log('No files selected');
            }
        });

    // 15. 批量上传处理
    let fileList = [];
    
    function handleBatchFiles(files) {
        batchResults = [];
        const newFiles = Array.from(files).filter(file => file.type.match('image.*'));
        if (newFiles.length === 0) {
            alert('请选择图片文件');
            return;
        }
        
        newFiles.forEach(file => {
            if (!fileList.some(f => f.name === file.name && f.size === file.size)) {
                fileList.push(file);
            }
        });
        
        updateFileListUI();
    }
    
    function updateFileListUI() {
        const fileListContainer = document.getElementById('file-list-items');
        fileListContainer.innerHTML = '';
        
        if (fileList.length === 0) {
            fileListContainer.innerHTML = '<p class="text-muted">暂无文件</p>';
            return;
        }
        
        fileList.forEach((file, index) => {
            const item = document.createElement('div');
            item.className = 'file-item d-flex justify-content-between align-items-center p-2';
            item.innerHTML = `
                <span>${file.name} (${(file.size/1024).toFixed(1)}KB)</span>
                <button class="btn btn-sm btn-outline-danger remove-btn" data-index="${index}">
                    <i class="bi bi-trash"></i>
                </button>
            `;
            fileListContainer.appendChild(item);
        });
        
        updateBatchFileInput();
    }
    
    function updateBatchFileInput() {
        const dataTransfer = new DataTransfer();
        fileList.forEach(file => dataTransfer.items.add(file));
        batchFileInput.files = dataTransfer.files;
    }
    
    document.addEventListener('click', function(e) {
        if (e.target.closest('.remove-btn')) {
            const index = parseInt(e.target.closest('.remove-btn').dataset.index);
            fileList.splice(index, 1);
            updateFileListUI();
        }
    });
    
    document.getElementById('clear-all-btn').addEventListener('click', function() {
        fileList = [];
        updateFileListUI();
    });

    batchDropArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        batchDropArea.style.borderColor = 'var(--primary-color)';
    });

    batchDropArea.addEventListener('dragleave', () => {
        batchDropArea.style.borderColor = 'var(--border-color)';
    });

    batchDropArea.addEventListener('drop', (e) => {
        e.preventDefault();
        batchDropArea.style.borderColor = 'var(--border-color)';
        if (e.dataTransfer.files.length) {
            handleBatchFiles(e.dataTransfer.files);
            batchFileInput.files = e.dataTransfer.files;
        }
    });

    batchDropArea.addEventListener('click', () => batchFileInput.click());
    batchFileInput.addEventListener('change', () => {
        if (batchFileInput.files.length) {
            handleBatchFiles(batchFileInput.files);
        }
    });
});
