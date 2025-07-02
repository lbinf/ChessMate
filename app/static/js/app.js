// 全局变量
let fileData = { buffer: null, name: null, type: null };
let currentHistory = [];
let previousHistory = [];

const CURRENT_HISTORY_KEY = 'chessHistory_current_v2';
const PREVIOUS_HISTORY_KEY = 'chessHistory_previous_v2';

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

// 初始化应用
function initializeApp() {
    setupDragAndDrop();
    setupFileInput();
    setupPasteEvents();
    loadHistories();
}

// 设置拖拽上传
function setupDragAndDrop() {
    const uploadArea = document.getElementById('uploadArea');
    
    uploadArea.addEventListener('dragover', function(e) {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });
    
    uploadArea.addEventListener('dragleave', function(e) {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
    });
    
    uploadArea.addEventListener('drop', function(e) {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFileSelect(files[0]);
        }
    });
}

// 设置文件输入
function setupFileInput() {
    const imageInput = document.getElementById('imageInput');
    imageInput.addEventListener('change', function(e) {
        if (e.target.files.length > 0) {
            handleFileSelect(e.target.files[0]);
        }
    });
}

// 设置粘贴事件
function setupPasteEvents() {
    document.addEventListener('paste', function(e) {
        const items = e.clipboardData.items;
        for (let i = 0; i < items.length; i++) {
            if (items[i].type.indexOf('image') !== -1) {
                const file = items[i].getAsFile();
                if (file) {
                    handleFileSelect(file);
                    showAlert('图片已从剪贴板粘贴', 'success');
                }
                break;
            }
        }
    });
}

// 粘贴图片函数（用于按钮点击）
async function pasteImage() {
    try {
        const clipboardItems = await navigator.clipboard.read();
        for (const clipboardItem of clipboardItems) {
            for (const type of clipboardItem.types) {
                if (type.startsWith('image/')) {
                    const blob = await clipboardItem.getType(type);
                    const file = new File([blob], 'pasted-image.png', { type: type });
                    handleFileSelect(file);
                    showAlert('图片已从剪贴板粘贴', 'success');
                    return;
                }
            }
        }
        showAlert('剪贴板中没有找到图片', 'warning');
    } catch (error) {
        console.error('粘贴图片失败:', error);
        showAlert('粘贴失败，请直接按 Ctrl+V 粘贴图片', 'warning');
    }
}

// 处理文件选择
function handleFileSelect(file) {
    if (!file.type.startsWith('image/')) {
        showAlert('请选择图片文件', 'error');
        return;
    }
    
    const reader = new FileReader();
    
    reader.onload = function(e) {
        fileData.buffer = e.target.result;
        fileData.name = file.name;
        fileData.type = file.type;
        
        const blob = new Blob([fileData.buffer], { type: fileData.type });
        const previewUrl = URL.createObjectURL(blob);
        
        const uploadArea = document.getElementById('uploadArea');
        
        const img = document.createElement('img');
        img.src = previewUrl;
        img.classList.add('img-fluid', 'rounded', 'mb-3');
        img.style.maxHeight = '200px';
        img.onload = function() {
            URL.revokeObjectURL(this.src);
        };
        
        uploadArea.innerHTML = '';
        uploadArea.appendChild(img);
        uploadArea.innerHTML += `
            <h6 class="text-success">${file.name}</h6>
            <button class="btn btn-outline-primary btn-sm mt-2" onclick="resetFileInput()">
                <i class="fas fa-times me-2"></i>重新选择
            </button>
        `;
    };
    
    reader.readAsArrayBuffer(file);
}
    
// 重置文件输入
function resetFileInput() {
    fileData = { buffer: null, name: null, type: null };
    const uploadArea = document.getElementById('uploadArea');
    uploadArea.innerHTML = `
        <i class="fas fa-cloud-upload-alt fa-3x text-primary mb-3"></i>
        <h5 class="mb-3">拖拽图片到此处或点击上传</h5>
        <p class="text-muted mb-3">支持 JPG、PNG 格式的棋盘截图</p>
        <p class="text-muted mb-3">
            <i class="fas fa-keyboard me-1"></i>
            也可以按 <kbd>Ctrl+V</kbd> 粘贴剪贴板中的图片
        </p>
        <input type="file" id="imageInput" accept="image/*" class="d-none">
        <button class="btn btn-primary me-2" onclick="document.getElementById('imageInput').click()">
            <i class="fas fa-upload me-2"></i>选择图片
        </button>
        <button class="btn btn-outline-primary" onclick="pasteImage()">
            <i class="fas fa-paste me-2"></i>粘贴图片
        </button>
    `;
    setupFileInput();
}
// 分析棋局
async function analyzeChess(params) {
    const fenInput = document.getElementById('fen-input');
    const fen = fenInput.value.trim();
    if(!fen){
        await analyzeImage()
    }else{
        await analyzeFenString()
    }
}
// 分析图片
async function analyzeImage() {

    if (!fileData.buffer) {
        showAlert('请先选择图片文件', 'error');
        return;
    }
    
    showLoading(true);
    
    try {
        const param = {
            platform: document.getElementById('platform').value,
            autoModel: document.getElementById('autoModel').value,
            goParam: document.getElementById('goParam').value,
            depth: document.getElementById('depth').value,
            movetime: document.getElementById('movetime').value
        };
       
        
        const formData = new FormData();

        const file = new File([fileData.buffer], fileData.name, { type: fileData.type });
        formData.append('image', file);        
        formData.append('param', JSON.stringify(param))
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData,
            cache: 'no-cache'
        });
        
        const data = await response.json();
        
        if (response.ok && data.result) {
            displayStructuredResult(data.result);
            addToHistory(data.result);
        } else {
            const errorMessage = data.error || `分析失败 (${response.status})`;
            showAlert(errorMessage, 'error');
        }
    } catch (error) {
        console.error('分析过程出错:', error);
        showAlert(`分析失败: ${error.message}`, 'error');
    } finally {
        showLoading(false);
    }
}
    
// 显示结构化的结果
function displayStructuredResult(resultData) {
    const { fen, chinese_move,move } = resultData;
    const nextMoveCard = document.getElementById('nextMoveCard');
    const nextMoveContent = document.getElementById('nextMoveContent');

    if (nextMoveCard && nextMoveContent) {
        nextMoveContent.innerHTML = `
            <p class="text-muted mb-2" style="font-size: 0.9rem;">AI 建议</p>
            <div style="font-size: 2.2rem; font-weight: bold; color: #28a745;">${chinese_move}</div>
            <div style="font-family: 'Courier New', Courier, monospace; color: #6c757d; margin-top: 0.5rem;">${fen}</div>
        `;
        nextMoveCard.classList.remove('d-none');
        nextMoveCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
    } else {
        console.error("UI elements 'nextMoveCard' or 'nextMoveContent' not found.");
    }
}

// 修改 addToHistory 和 updateHistoryDisplay 以处理新数据结构
function addToHistory(resultData) {
    const newRecord = {
        timestamp: new Date().toISOString(),
        fen: resultData.fen,
        move: resultData.chinese_move,
        platform: document.getElementById('platform').value
    };
    
    if (currentHistory.length === 0 || currentHistory[0].fen !== newRecord.fen) {
        currentHistory.unshift(newRecord);
    }
    
    if (currentHistory.length > 20) {
        currentHistory.pop();
    }
    
    updateHistoryDisplay(document.getElementById('historyList'), currentHistory, '暂无历史记录');
    saveHistories();
}

function updateHistoryDisplay(listElement, historyArray, emptyMessage) {
    if (!listElement) return;

    if (historyArray.length === 0) {
        listElement.innerHTML = `<p class="text-center text-muted mt-3">${emptyMessage}</p>`;
        return;
    }
    
    listElement.innerHTML = historyArray.map(record => `
        <div class="list-group-item list-group-item-action">
            <div class="d-flex w-100 justify-content-between">
                <h6 class="mb-1">${record.move}</h6>
                <small class="text-muted">${new Date(record.timestamp).toLocaleTimeString()}</small>
            </div>
            <p class="mb-1 small" style="font-family: 'Courier New', monospace;">${record.fen}</p>
            <small class="badge bg-secondary">${record.platform}</small>
        </div>
    `).join('');
}


// 保存历史记录
function saveHistories() {
    localStorage.setItem(CURRENT_HISTORY_KEY, JSON.stringify(currentHistory));
    localStorage.setItem(PREVIOUS_HISTORY_KEY, JSON.stringify(previousHistory));
}

// 加载历史记录
function loadHistories() {
    currentHistory = JSON.parse(localStorage.getItem(CURRENT_HISTORY_KEY)) || [];
    previousHistory = JSON.parse(localStorage.getItem(PREVIOUS_HISTORY_KEY)) || [];
    updateHistoryDisplay(document.getElementById('historyList'), currentHistory, '暂无历史记录');
    updateHistoryDisplay(document.getElementById('previousHistoryList'), previousHistory, '没有上一局的记录');
}

// 新游戏
function newGame() {
    if (currentHistory.length > 0) {
        previousHistory = [...currentHistory];
        updateHistoryDisplay(document.getElementById('previousHistoryList'), previousHistory, '没有上一局的记录');
    }

    currentHistory = [];
    updateHistoryDisplay(document.getElementById('historyList'), currentHistory, '暂无历史记录');
    
    saveHistories();

    resetFileInput();
    const nextMoveCard = document.getElementById('nextMoveCard');
    if(nextMoveCard) nextMoveCard.classList.add('d-none');
    showAlert('新游戏已开始！当前棋局历史已归档。', 'success');
}

// 调整参数
function adjustParameter(paramName, isAdd) {
    const input = document.getElementById(paramName);
    let value = parseInt(input.value);
    
    if (paramName === 'depth') {
        value += isAdd ? 5 : -5;
        value = Math.max(5, Math.min(200, value));
    } else if (paramName === 'movetime') {
        value += isAdd ? 5000 : -5000;
        value = Math.max(3000, Math.min(40000, value));
    }
    
    input.value = value;
}

// 重置参数
async function resetParameters() {
    try {
        const response = await fetch('/change_parameter', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: 'is_add=default'
        });
        const result = await response.json();
        if (response.ok) {
            document.getElementById('depth').value = result.message.value.depth;
            document.getElementById('movetime').value = result.message.value.movetime;
            showAlert('参数已恢复默认', 'success');
        } else {
            showAlert('重置参数失败', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showAlert('网络错误，请重试', 'error');
    }
}

// 显示加载状态
function showLoading(show) {
    const loading = document.getElementById('loading');
    const analyzeBtn = document.getElementById('analyzeBtn');
    
    if (show) {
        loading.style.display = 'block';
        analyzeBtn.disabled = true;
        analyzeBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>分析中...';
    } else {
        loading.style.display = 'none';
        analyzeBtn.disabled = false;
        analyzeBtn.innerHTML = '<i class="fas fa-brain me-2"></i>分析棋局';
    }
}

// 显示提示信息
function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    alertDiv.innerHTML = `${message}<button type="button" class="btn-close" data-bs-dismiss="alert"></button>`;
    document.body.appendChild(alertDiv);
    
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 3000);
}

// 键盘快捷键
document.addEventListener('keydown', function(e) {
    if (e.ctrlKey && e.key === 'Enter') {
        e.preventDefault();
        analyzeImage();
    }
    
    if (e.key === 'Escape') {
        resetFileInput();
    }
});

async function analyzeFenString() {
    const fenInput = document.getElementById('fen-input');
    const fen = fenInput.value.trim();

    if (!fen) {
        showAlert('Please enter a FEN string.');
        return;
    }

    showLoading(true, 'Analyzing FEN...');
    try {
        const response = await fetch('/api/analyze_fen', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ fen: fen })
        })
        
        const data = await response.json();
        
        if (response.ok && data.result) {
            displayStructuredResult(data.result);
            addToHistory(data.result);
        } else {
            const errorMessage = data.error || `分析失败 (${response.status})`;
            showAlert(errorMessage, 'error');
        }

    } catch (error) {
        console.error('分析过程出错:', error);
        showAlert(`分析失败: ${error.message}`, 'error');
    } finally {
        showLoading(false);
    }
}

function clearFenInput() {
    const fenInput = document.getElementById('fen-input');
    if (fenInput) {
        fenInput.value = '';
        fenInput.focus();
    }
}



