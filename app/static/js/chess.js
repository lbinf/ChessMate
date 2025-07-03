// chess.js
// 依赖 config.js 提供的全局配置和规则
// 实现棋盘渲染、交互、FEN/UCI解析、UI事件、状态管理等中国象棋核心功能
// ...（此处应为index.html中相关JS的迁移实现，详见原始index.html） 

// ====== 主题等级调节与主题切换 ======
document.getElementById('themeSelect').addEventListener('change', function() {
    updateTheme();
});
document.getElementById('themeLevelSlider').addEventListener('input', function() {
    const level = parseInt(this.value);
    document.getElementById('themeLevelValue').textContent = level;
    setThemeLevel(level);
});
document.getElementById('themeLevelSlider').max = 16;

// ====== 棋盘与状态初始化 ======
// 棋盘参数和状态
let currentTheme = getScaledTheme(themes.default);
let CELL_SIZE = currentTheme.cellSize;
let BOARD_PADDING = currentTheme.boardPadding;
let COORD_FONT_SIZE = currentTheme.coordFontSize;
let COORD_MARGIN_TOP = currentTheme.coordMarginTop;
let COORD_MARGIN_BOTTOM = currentTheme.coordMarginBottom;
let COORD_COLOR = currentTheme.coordColor;
let COORD_OUTER_MARGIN = currentTheme.coordOuterMargin;
let COORD_TO_BOARD_GAP = currentTheme.coordToBoardGap;
let COORD_TO_BOARD_GAP_BOTTOM = currentTheme.coordToBoardGapBottom;
let COORD_AREA_HEIGHT = COORD_FONT_SIZE + COORD_MARGIN_TOP + COORD_MARGIN_BOTTOM;
const NUM_FILES = 9;
const NUM_RANKS = 10;

function initializeBoardState() {
    const board = Array.from({length: 10}, () => Array(9).fill(''));
    [
        ['R_车', 0, 0], ['R_马', 1, 0], ['R_相', 2, 0], ['R_仕', 3, 0], ['R_帅', 4, 0], ['R_仕', 5, 0], ['R_相', 6, 0], ['R_马', 7, 0], ['R_车', 8, 0],
        ['R_炮', 1, 2], ['R_炮', 7, 2],
        ['R_兵', 0, 3], ['R_兵', 2, 3], ['R_兵', 4, 3], ['R_兵', 6, 3], ['R_兵', 8, 3]
    ].forEach(([piece, x, y]) => { board[y][x] = piece; });
    [
        ['B_车', 0, 9], ['B_马', 1, 9], ['B_象', 2, 9], ['B_士', 3, 9], ['B_将', 4, 9], ['B_士', 5, 9], ['B_象', 6, 9], ['B_马', 7, 9], ['B_车', 8, 9],
        ['B_炮', 1, 7], ['B_炮', 7, 7],
        ['B_卒', 0, 6], ['B_卒', 2, 6], ['B_卒', 4, 6], ['B_卒', 6, 6], ['B_卒', 8, 6]
    ].forEach(([piece, x, y]) => { board[y][x] = piece; });
    return board;
}
let selectedPiece = null;
let hoverCell = null;
let flipBoard = false;
let boardState = initializeBoardState();

// ...（此处继续迁移所有棋盘渲染、交互、FEN/UCI解析、UI事件、状态管理等JS实现，详见原始index.html <script>内容）

document.addEventListener('DOMContentLoaded', function() {
    autoFitThemeLevel();
    updateTheme();
    loadHistory();
    let step = currentStep;
    if (moveList.length > 0) {
        if (step < 0) step = 0;
        if (step > moveList.length) step = moveList.length;
        restoreToStep(step);
    } else {
        setFEN(initialFEN);
    }
    updateMoveButtons();
    // 其它初始化逻辑...
});

// ...（此处省略，实际应迁移全部棋盘渲染、交互、FEN/UCI解析、UI事件、状态管理等JS实现） 

// ====== 棋盘渲染与视觉坐标映射 ======
// 棋盘canvas和上下文
const canvas = document.getElementById('chessboardCanvas');
const ctx = canvas.getContext('2d');

// 视觉坐标映射
function toCanvasCoord(row, col, forLabel = false) {
    let drawCol, drawRow;
    if (!flipBoard) {
        drawCol = col;
        drawRow = NUM_RANKS - 1 - row;
    } else {
        drawCol = NUM_FILES - 1 - col;
        drawRow = row;
    }
    const x = BOARD_PADDING + drawCol * CELL_SIZE;
    const y = BOARD_PADDING + drawRow * CELL_SIZE + COORD_AREA_HEIGHT + COORD_OUTER_MARGIN;
    return {x, y};
}

// 主题更新
function updateTheme() {
    const baseThemeName = document.getElementById('themeSelect').value;
    currentTheme = getScaledTheme(themes[baseThemeName]);
    CELL_SIZE = currentTheme.cellSize;
    BOARD_PADDING = currentTheme.boardPadding;
    COORD_FONT_SIZE = currentTheme.coordFontSize;
    COORD_MARGIN_TOP = currentTheme.coordMarginTop;
    COORD_MARGIN_BOTTOM = currentTheme.coordMarginBottom;
    COORD_COLOR = currentTheme.coordColor;
    COORD_OUTER_MARGIN = currentTheme.coordOuterMargin;
    COORD_TO_BOARD_GAP = currentTheme.coordToBoardGap;
    COORD_TO_BOARD_GAP_BOTTOM = currentTheme.coordToBoardGapBottom;
    COORD_AREA_HEIGHT = COORD_FONT_SIZE + COORD_MARGIN_TOP + COORD_MARGIN_BOTTOM;
    // 重新计算棋盘尺寸
    const BOARD_INNER_WIDTH = (NUM_FILES - 1) * CELL_SIZE;
    const BOARD_INNER_HEIGHT = (NUM_RANKS - 1) * CELL_SIZE;
    // 更新canvas尺寸
    canvas.width = BOARD_INNER_WIDTH + BOARD_PADDING * 2;
    canvas.height = BOARD_INNER_HEIGHT + BOARD_PADDING * 2 + COORD_AREA_HEIGHT * 2 + COORD_OUTER_MARGIN * 2;
    // 更新UI样式
    document.body.style.background = currentTheme.boardBg;
    document.getElementById('statusBar').style.background = currentTheme.statusBarBg;
    document.getElementById('statusBar').style.color = currentTheme.statusBarColor;
    // 重绘棋盘
    drawBoard();
}

// 棋盘绘制
function drawBoard() {
    const BOARD_INNER_WIDTH = (NUM_FILES - 1) * CELL_SIZE;
    const BOARD_INNER_HEIGHT = (NUM_RANKS - 1) * CELL_SIZE;
    ctx.fillStyle = currentTheme.boardBg;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.strokeStyle = currentTheme.boardBorderColor;
    ctx.lineWidth = currentTheme.boardBorderWidth;
    ctx.strokeRect(BOARD_PADDING-currentTheme.reactPadding, BOARD_PADDING-currentTheme.reactPadding + COORD_AREA_HEIGHT + COORD_OUTER_MARGIN, 
        BOARD_INNER_WIDTH+currentTheme.reactPadding*2, BOARD_INNER_HEIGHT+currentTheme.reactPadding*2);
    ctx.lineWidth = currentTheme.boardLineWidth;
    ctx.strokeStyle = currentTheme.boardLineColor;
    // 竖线
    for (let c = 0; c < NUM_FILES; c++) {
        ctx.beginPath();
        const {x} = toCanvasCoord(0, c);
        if (c >= 1 && c <= 7) {
            ctx.moveTo(x, BOARD_PADDING + COORD_AREA_HEIGHT + COORD_OUTER_MARGIN);
            ctx.lineTo(x, BOARD_PADDING + 4 * CELL_SIZE + COORD_AREA_HEIGHT + COORD_OUTER_MARGIN);
            ctx.stroke();
            ctx.beginPath();
            ctx.moveTo(x, BOARD_PADDING + 5 * CELL_SIZE + COORD_AREA_HEIGHT + COORD_OUTER_MARGIN);
            ctx.lineTo(x, BOARD_PADDING + BOARD_INNER_HEIGHT + COORD_AREA_HEIGHT + COORD_OUTER_MARGIN);
            ctx.stroke();
        } else {
            ctx.moveTo(x, BOARD_PADDING + COORD_AREA_HEIGHT + COORD_OUTER_MARGIN);
            ctx.lineTo(x, BOARD_PADDING + BOARD_INNER_HEIGHT + COORD_AREA_HEIGHT + COORD_OUTER_MARGIN);
            ctx.stroke();
        }
    }
    // 横线
    for (let r = 0; r < NUM_RANKS; r++) {
        ctx.beginPath();
        const y = BOARD_PADDING + r * CELL_SIZE + COORD_AREA_HEIGHT + COORD_OUTER_MARGIN;
        ctx.moveTo(BOARD_PADDING, y);
        ctx.lineTo(BOARD_PADDING + BOARD_INNER_WIDTH, y);
        ctx.stroke();
    }
    // 宫区对角线
    function palaceLine(row1, col1, row2, col2) {
        const p1 = toCanvasCoord(row1, col1);
        const p2 = toCanvasCoord(row2, col2);
        ctx.beginPath();
        ctx.moveTo(p1.x, p1.y);
        ctx.lineTo(p2.x, p2.y);
        ctx.stroke();
    }
    palaceLine(0, 3, 2, 5);
    palaceLine(0, 5, 2, 3);
    palaceLine(7, 3, 9, 5);
    palaceLine(7, 5, 9, 3);
    // 坐标标注
    ctx.font = `bold ${COORD_FONT_SIZE}px 'Microsoft YaHei', '微软雅黑', Arial, sans-serif`;
    ctx.fillStyle = COORD_COLOR;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    const chineseNumerals = ['一', '二', '三', '四', '五', '六', '七', '八', '九'];
    let bottomY = canvas.height - COORD_OUTER_MARGIN - COORD_TO_BOARD_GAP + COORD_TO_BOARD_GAP_BOTTOM;
    if (!flipBoard) {
        for (let i = 0; i < NUM_FILES; i++) {
            const {x} = toCanvasCoord(0, NUM_FILES - 1 - i, true);
            ctx.fillText(chineseNumerals[i], x, bottomY);
        }
    } else {
        for (let i = 0; i < NUM_FILES; i++) {
            const {x} = toCanvasCoord(0, i, true);
            ctx.fillText((i + 1).toString(), x, bottomY);
        }
    }
    let topY = COORD_OUTER_MARGIN + COORD_AREA_HEIGHT + COORD_TO_BOARD_GAP;
    if (!flipBoard) {
        for (let i = 0; i < NUM_FILES; i++) {
            const {x} = toCanvasCoord(0, i, true);
            ctx.fillText((i + 1).toString(), x, topY);
        }
    } else {
        for (let i = 0; i < NUM_FILES; i++) {
            const {x} = toCanvasCoord(0, NUM_FILES - 1 - i, true);
            ctx.fillText(chineseNumerals[i], x, topY);
        }
    }
    // 河界文字
    if (currentTheme.riverText) {
        currentTheme.riverText.forEach(cfg => {
            ctx.save();
            ctx.globalAlpha = cfg.alpha ?? 1;
            ctx.font = cfg.font;
            ctx.fillStyle = cfg.color;
            ctx.textAlign = "center";
            ctx.textBaseline = "middle";
            const {x, y} = toCanvasCoord(cfg.y, cfg.x, true);
            ctx.fillText(cfg.text, x, y);
            ctx.restore();
        });
    }
    // L角标记
    function drawLCorner(cx, cy, hDir, vDir, color, width, len, gap) {
        ctx.save();
        ctx.strokeStyle = color;
        ctx.lineWidth = width;
        ctx.beginPath();
        ctx.moveTo(cx + hDir * gap, cy + vDir * gap);
        ctx.lineTo(cx + hDir * (gap + len), cy + vDir * gap);
        ctx.moveTo(cx + hDir * gap, cy + vDir * gap);
        ctx.lineTo(cx + hDir * gap, cy + vDir * (gap + len));
        ctx.stroke();
        ctx.restore();
    }
    const lMarkPos = [
        {row: 2, col: 1}, {row: 2, col: 7}, {row: 7, col: 1}, {row: 7, col: 7},
        {row: 3, col: 0}, {row: 3, col: 2}, {row: 3, col: 4}, {row: 3, col: 6}, {row: 3, col: 8},
        {row: 6, col: 0}, {row: 6, col: 2}, {row: 6, col: 4}, {row: 6, col: 6}, {row: 6, col: 8}
    ];
    lMarkPos.forEach(pos => {
        const {x, y} = toCanvasCoord(pos.row, pos.col);
        const gap = currentTheme.lMarkGap;
        if (pos.col === 0) {
            if(flipBoard){
                drawLCorner(x, y, -1, -1, currentTheme.lMarkColor, currentTheme.lMarkWidth, currentTheme.lMarkLength, gap);
                drawLCorner(x, y, -1, 1, currentTheme.lMarkColor, currentTheme.lMarkWidth, currentTheme.lMarkLength, gap);
            }else{
                drawLCorner(x, y, 1, 1, currentTheme.lMarkColor, currentTheme.lMarkWidth, currentTheme.lMarkLength, gap);
                drawLCorner(x, y, 1, -1, currentTheme.lMarkColor, currentTheme.lMarkWidth, currentTheme.lMarkLength, gap);
            }
        } else if (pos.col === 8) {
            if(flipBoard){
                drawLCorner(x, y, 1, 1, currentTheme.lMarkColor, currentTheme.lMarkWidth, currentTheme.lMarkLength, gap);
                drawLCorner(x, y, 1, -1, currentTheme.lMarkColor, currentTheme.lMarkWidth, currentTheme.lMarkLength, gap);
            }else{
                drawLCorner(x, y, -1, 1, currentTheme.lMarkColor, currentTheme.lMarkWidth, currentTheme.lMarkLength, gap);
                drawLCorner(x, y, -1, -1, currentTheme.lMarkColor, currentTheme.lMarkWidth, currentTheme.lMarkLength, gap);
            }
        } else {
            drawLCorner(x, y, 1, 1, currentTheme.lMarkColor, currentTheme.lMarkWidth, currentTheme.lMarkLength, gap);
            drawLCorner(x, y, -1, 1, currentTheme.lMarkColor, currentTheme.lMarkWidth, currentTheme.lMarkLength, gap);
            drawLCorner(x, y, 1, -1, currentTheme.lMarkColor, currentTheme.lMarkWidth, currentTheme.lMarkLength, gap);
            drawLCorner(x, y, -1, -1, currentTheme.lMarkColor, currentTheme.lMarkWidth, currentTheme.lMarkLength, gap);
        }
    });
    // 棋子
    drawPieces();
    // 选中高亮
    if (selectedPiece) {
        const {x, y} = toCanvasCoord(selectedPiece.row, selectedPiece.col);
        ctx.strokeStyle = currentTheme.highlightColor;
        ctx.lineWidth = currentTheme.highlightWidth;
        ctx.beginPath();
        ctx.arc(x, y, CELL_SIZE * currentTheme.pieceRadiusRatio, 0, Math.PI * 2);
        ctx.stroke();
    }
    // hover高亮
    if (hoverCell) {
        const {x, y} = toCanvasCoord(hoverCell.row, hoverCell.col);
        ctx.strokeStyle = currentTheme.hoverColor;
        ctx.lineWidth = currentTheme.hoverWidth;
        ctx.beginPath();
        ctx.arc(x, y, CELL_SIZE * currentTheme.pieceRadiusRatio * 0.9, 0, Math.PI * 2);
        ctx.stroke();
    }
}

function drawPieces() {
    ctx.font = currentTheme.pieceFont;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    for (let row = 0; row < boardState.length; row++) {
        for (let col = 0; col < boardState[row].length; col++) {
            const pieceCode = boardState[row][col];
            if (pieceCode !== '') {
                const pieceChar = pieceCharMap[pieceCode];
                const {x, y} = toCanvasCoord(row, col);
                const pieceRadius = CELL_SIZE * currentTheme.pieceRadiusRatio;
                let pieceBackgroundColor, pieceTextColor;
                if (pieceCode.startsWith('R_')) {
                    pieceBackgroundColor = currentTheme.pieceRedBg;
                    pieceTextColor = currentTheme.pieceTextColor;
                } else {
                    pieceBackgroundColor = currentTheme.pieceBlackBg;
                    pieceTextColor = currentTheme.pieceTextColor;
                }
                ctx.beginPath();
                ctx.arc(x, y, pieceRadius, 0, Math.PI * 2);
                ctx.fillStyle = pieceBackgroundColor;
                ctx.fill();
                ctx.strokeStyle = 'rgba(0, 0, 0, 0.4)';
                ctx.lineWidth = 1;
                ctx.stroke();
                ctx.fillStyle = pieceTextColor;
                ctx.fillText(pieceChar, x, y);
            }
        }
    }
}

// 1. 视觉坐标映射、棋盘绘制、棋子绘制
// 2. 事件绑定（canvas点击、hover、按钮、输入框等）
// 3. FEN/UCI解析、走子、状态栏、侧边栏、弹窗等
// 4. 自动初始化

// ...（此处为完整迁移内容，详见原始index.html <script>） 

// ====== 棋盘交互与事件绑定 ======
function getCellFromMouseEvent(event) {
    const rect = canvas.getBoundingClientRect();
    const mouseX = event.clientX - rect.left;
    const mouseY = event.clientY - rect.top;
    let bestCell = null;
    let minDist = Infinity;
    for (let row = 0; row < NUM_RANKS; row++) {
        for (let col = 0; col < NUM_FILES; col++) {
            const piece = boardState[row][col];
            if (piece) {
                const {x, y} = toCanvasCoord(row, col);
                const dx = mouseX - x;
                const dy = mouseY - y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                const pieceRadius = CELL_SIZE * currentTheme.pieceRadiusRatio * 1.18;
                if (dist <= pieceRadius && dist < minDist) {
                    bestCell = {row, col};
                    minDist = dist;
                }
            }
        }
    }
    if (!bestCell) {
        let col, row;
        if (!flipBoard) {
            col = Math.round((mouseX - BOARD_PADDING) / CELL_SIZE);
            row = NUM_RANKS - 1 - Math.round((mouseY - BOARD_PADDING) / CELL_SIZE);
        } else {
            col = NUM_FILES - 1 - Math.round((mouseX - BOARD_PADDING) / CELL_SIZE);
            row = Math.round((mouseY - BOARD_PADDING) / CELL_SIZE);
        }
        if (row >= 0 && row < NUM_RANKS && col >= 0 && col < NUM_FILES) {
            bestCell = {row, col};
        }
    }
    return bestCell;
}
let lastHoverCell = null;
canvas.addEventListener('mousemove', (event) => {
    const cell = getCellFromMouseEvent(event);
    hoverCell = cell;
    if (cell && (lastHoverCell === null || cell.row !== lastHoverCell.row || cell.col !== lastHoverCell.col)) {
        let status = `坐标: (${cell.col},${cell.row})`;
        const piece = boardState[cell.row][cell.col];
        if (piece) {
            status += ` | 棋子: ${piece}(${pieceCharMap[piece]})`;
        }
        document.getElementById('statusBar').textContent = status;
        lastHoverCell = cell;
    }
    if (!cell) {
        document.getElementById('statusBar').textContent = '状态栏';
        lastHoverCell = null;
    }
    drawBoard();
});
canvas.addEventListener('mouseleave', () => {
    hoverCell = null;
    lastHoverCell = null;
    document.getElementById('statusBar').textContent = '状态栏';
    drawBoard();
});
canvas.addEventListener('click', (event) => {
    const cell = getCellFromMouseEvent(event);
    if (!cell) return;
    const piece = boardState[cell.row][cell.col];
    if (selectedPiece) {
        if (selectedPiece.row === cell.row && selectedPiece.col === cell.col) {
            selectedPiece = null;
            drawBoard();
        } else {
            const fromUci = Object.entries(fileMap).find(([k,v])=>v===selectedPiece.col)[0] + selectedPiece.row;
            const toUci = Object.entries(fileMap).find(([k,v])=>v===cell.col)[0] + cell.row;
            const uciStr = fromUci + toUci;
            moveUCI(uciStr);
            selectedPiece = null;
        }
    } else if (piece) {
        if ((currentTurn === 'w' && piece.startsWith('R_')) || (currentTurn === 'b' && piece.startsWith('B_'))) {
            selectedPiece = {row: cell.row, col: cell.col};
            drawBoard();
        }
    }
});
function toggleFlipBoard() {
    flipBoard = !flipBoard;
    drawBoard();
}

// ====== 按钮与UI事件绑定 ======
document.getElementById('fenInputBtn').onclick = function() {
    document.getElementById('fenModal').style.display = 'flex';
    document.getElementById('fenModalInput').value = '';
};
document.getElementById('fenModalOk').onclick = function() {
    const fen = document.getElementById('fenModalInput').value.trim();
    if (fen) setFEN(fen);
    document.getElementById('fenModal').style.display = 'none';
};
document.getElementById('fenModalCancel').onclick = function() {
    document.getElementById('fenModal').style.display = 'none';
};
document.getElementById('fenCopyBtn').onclick = function() {
    const fen = getFEN();
    navigator.clipboard.writeText(fen).then(() => {
        document.getElementById('moveMsg').textContent = '已复制FEN';
    });
};
document.getElementById('resetBtn').onclick = function() {
    setFEN(initialFEN);
    moveList = [];
    moveListZh = [];
    moveListFen = [];
    currentStep = 0;
    const panel = document.getElementById('moveListZhPanel');
    if (panel) panel.innerHTML = '';
    saveHistory();
};
document.getElementById('clearBtn').onclick = function() {
    boardState = Array.from({length: NUM_RANKS}, () => Array(NUM_FILES).fill(''));
    drawBoard();
};
document.getElementById('flipBtn').onclick = function() {
    toggleFlipBoard();
};
document.getElementById('uciMoveBtn').onclick = function() {
    const uci = document.getElementById('uciInput').value.trim();
    if (!uci) return;
    const ok = moveUCI(uci);
    if (ok) {
        document.getElementById('moveMsg').textContent = '走子成功';
    } else {
        document.getElementById('moveMsg').textContent = '走子不合法';
    }
};
document.getElementById('newGameBtn').onclick = function() {
    resetChess()
    setFEN(initialFEN, false);
    document.getElementById('ai-move').style.display='none'
};

function resetChess(){
    moveList = [];
    moveListZh = [];
    moveListFen = [];
    currentStep = 0;
    localStorage.removeItem('moveList');
    localStorage.removeItem('currentStep');
    const panel = document.getElementById('moveListZhPanel');
    if (panel) panel.innerHTML = '';
    updateMoveButtons();
}

// ====== FEN/UCI解析、走子、状态栏、棋谱、弹窗 ======
const initialFEN = 'rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w';
let currentTurn = 'w'; // 'w'红方，'b'黑方
let moveList = [];
let moveListZh = [];
let moveListFen = [];
let currentStep = 0;

function getFEN() {
    const pieceChar = {
        'R_车': 'R', 'R_马': 'N', 'R_相': 'B', 'R_仕': 'A', 'R_帅': 'K', 'R_炮': 'C', 'R_兵': 'P',
        'B_车': 'r', 'B_马': 'n', 'B_象': 'b', 'B_士': 'a', 'B_将': 'k', 'B_炮': 'c', 'B_卒': 'p'
    };
    let rows = [];
    for (let r = 9; r >= 0; r--) {
        let row = '';
        let empty = 0;
        for (let c = 0; c < 9; c++) {
            const p = boardState[r][c];
            if (!p) {
                empty++;
            } else {
                if (empty > 0) { row += empty; empty = 0; }
                row += pieceChar[p] || '';
            }
        }
        if (empty > 0) row += empty;
        rows.push(row);
    }
    return rows.join('/') + ' ' + currentTurn;
}
function setFEN(fenStr, keepMoveList) {
    const {board, turn} = parseXiangqiFEN(fenStr);
    boardState = board;
    currentTurn = turn;
    selectedPiece = null;
    if (!keepMoveList) {
        moveList = [];
        moveListZh = [];
        moveListFen = [];
    }
    drawBoard();
    updateSideIndicator();
    updateStatusPanel();
    updateMoveButtons();
}
function updateSideIndicator() {
    const indicator = document.getElementById('sideIndicator');
    const icon = indicator.querySelector('.piece-icon');
    if (currentTurn === 'w') {
        indicator.className = 'side-indicator red';
        icon.textContent = '帅';
        icon.style.color = '#d32f2f';
        icon.style.borderColor = '#d32f2f';
        indicator.style.bottom = '0';
        indicator.style.top = '';
    } else {
        indicator.className = 'side-indicator black';
        icon.textContent = '将';
        icon.style.color = '#222';
        icon.style.borderColor = '#222';
        indicator.style.top = '0';
        indicator.style.bottom = '';
    }
}
function updateStatusPanel(moveObj, append) {
   if(!moveObj){
        return
    }
    const panel = document.getElementById('moveListZhPanel');
    panel.insertAdjacentHTML('beforeend', moveRowHtml(moveObj, false));   
}
function moveRowHtml(m, isActive) {
    const color = m.is_move === 'w' ? '#d32f2f' : '#222';
    const activeStyle = isActive ? 'background:#ffe082;' : '';
    return `<tr style="border:1px solid #bbb;${activeStyle}">
        <td style="border:1px solid #bbb;">${m.num}</td>
        <td style="border:1px solid #bbb;color:${color};">${m.move_chinese}</td>
        <td style="border:1px solid #bbb;color:${color};">${m.move}</td>
        <td style="border:1px solid #bbb;font-size:12px;color:#888;">${m.fen}</td>
    </tr>`;
}
function uciToCoords(uci) {
    function parse(pos) {
        const col = fileMap[pos[0]];
        const row = parseInt(pos[1]);
        return {row, col};
    }
    return {from: parse(uci.slice(0,2)), to: parse(uci.slice(2,4))};
}
function moveUCI(uciStr) {
    const {from, to} = uciToCoords(uciStr);
    const piece = boardState[from.row][from.col];
    if (!piece) return false;
    if (!isLegalMove(boardState, from, to)) return false;
    const turnBeforeMove = currentTurn;
    boardState[to.row][to.col] = piece;
    boardState[from.row][from.col] = '';
    selectedPiece = null;
    currentTurn = (currentTurn === 'w') ? 'b' : 'w';

    // 如果当前不是在最后一步，截断moveList
    if (currentStep < moveList.length) {
        moveList = moveList.slice(0, currentStep);
    }

    const moveNum = moveList.length + 1;
    const moveObj = {
        num: moveNum,
        move: uciStr,
        move_chinese: uciToZh(uciStr, piece, turnBeforeMove),
        fen: getFEN(),
        is_move: turnBeforeMove
    };
    moveList.push(moveObj);

    // currentStep始终指向最新一步
    currentStep = moveList.length;

    drawBoard();
    updateSideIndicator();
    updateStatusPanel(moveObj, true);
    updateMoveButtons();
    saveHistory(); // 每次走棋后保存
    return true;
}
function uciToZh(uci, piece, turnBeforeMove) {
    const colMapHan = ['九','八','七','六','五','四','三','二','一'];
    const colMapNum = ['1','2','3','4','5','6','7','8','9'];
    const pieceCharMap = {
        'R_车': '车', 'R_马': '马', 'R_相': '相', 'R_仕': '仕', 'R_帅': '帅', 'R_炮': '炮', 'R_兵': '兵',
        'B_车': '车', 'B_马': '马', 'B_象': '象', 'B_士': '士', 'B_将': '将', 'B_炮': '炮', 'B_卒': '卒'
    };
    const pieceZh = piece ? pieceCharMap[piece] : '';
    const fromCol = uci[0];
    const fromRow = uci[1];
    const toCol = uci[2];
    const toRow = uci[3];
    let moveZh = '';
    if (pieceZh) {
        if (turnBeforeMove === 'w') {
            moveZh += '<span style="color:#d32f2f">红</span>';
            moveZh += pieceZh;
            moveZh += colMapHan[fileMap[fromCol]];
            if (fromRow === toRow) {
                moveZh += '平' + colMapHan[fileMap[toCol]];
            } else if (pieceZh === '马' || pieceZh === '相' || pieceZh === '仕') {
                if (toRow > fromRow) moveZh += '进' + colMapHan[fileMap[toCol]];
                else moveZh += '退' + colMapHan[fileMap[toCol]];
            } else {
                if (toRow > fromRow) moveZh += '进' + (parseInt(toRow)-parseInt(fromRow));
                else moveZh += '退' + (parseInt(fromRow)-parseInt(toRow));
            }
        } else {
            moveZh += '<span style="color:#222">黑</span>';
            moveZh += pieceZh;
            moveZh += colMapNum[fileMap[fromCol]];
            if (fromRow === toRow) {
                moveZh += '平' + colMapNum[fileMap[toCol]];
            } else if (pieceZh === '马' || pieceZh === '象' || pieceZh === '士') {
                if (toRow < fromRow) moveZh += '进' + colMapNum[fileMap[toCol]];
                else moveZh += '退' + colMapNum[fileMap[toCol]];
            } else {
                if (toRow < fromRow) moveZh += '进' + (parseInt(fromRow)-parseInt(toRow));
                else moveZh += '退' + (parseInt(toRow)-parseInt(fromRow));
            }
        }
        return moveZh;
    }
    return uci;
}
// 弹窗美化与复用
function showCustomModal(msg) {
    document.getElementById('customModalMsg').innerHTML = msg;
    document.getElementById('customModal').style.display = 'flex';
}
document.getElementById('customModalOk').onclick = function() {
    document.getElementById('customModal').style.display = 'none';
};
// 棋谱步数指针与本地存储、恢复、按钮状态等辅助函数可继续迁移...

// ...（后续继续迁移FEN/UCI解析、走子、状态栏、弹窗等） 

// ====== 自动适配主题等级 ======
function autoFitThemeLevel() {
    const NUM_FILES = 9;
    const boardPaddingRatio = themeRatios.boardPadding;
    let container = document.querySelector('.board-container');
    let maxWidth = container ? container.clientWidth : window.innerWidth;
    const cellSizeUnit = (NUM_FILES - 1) + 2 * boardPaddingRatio;
    let bestLevel = Math.floor(maxWidth / (cellSizeUnit * 3));
    bestLevel = Math.max(6, Math.min(THEME_LEVELS, bestLevel));
    document.getElementById('themeLevelSlider').value = bestLevel;
    document.getElementById('themeLevelValue').textContent = bestLevel;
    setThemeLevel(bestLevel);
}

function setThemeLevel(level) {
    window.themeLevel = Math.max(1, Math.min(THEME_LEVELS, level));
    updateTheme();
}

function updateMoveButtons() {
    const prevBtn = document.getElementById('prevMoveBtn');
    const nextBtn = document.getElementById('nextMoveBtn');
    if (prevBtn) prevBtn.disabled = !(moveList.length > 0 && currentStep > 1);
    if (nextBtn) nextBtn.disabled = !(moveList.length > 0 && currentStep < moveList.length);
}

function saveHistory() {
    localStorage.setItem('moveList', JSON.stringify(moveList));
    localStorage.setItem('currentStep', currentStep);
}
function loadHistory() {
    const ml = localStorage.getItem('moveList');
    const cs = localStorage.getItem('currentStep');
    moveList = ml ? JSON.parse(ml) : [];
    currentStep = cs ? parseInt(cs) : 0;
}
function restoreToStep(step) {
    let fen = initialFEN;
    let highlightIdx = step-1;
    if (moveList.length > 0 && (step <= 0 || step > moveList.length)) {
        fen = moveList[moveList.length-1].fen;
        highlightIdx = moveList.length-1;
        step = moveList.length;
    } else if (step > 0 && moveList.length >= step) {
        fen = moveList[step-1].fen;
        highlightIdx = step-1;
    }
    setFEN(fen, true);
    const panel = document.getElementById('moveListZhPanel');
    panel.innerHTML = '';
    for (let i = 0; i < moveList.length; i++) {
        panel.insertAdjacentHTML('beforeend', moveRowHtml(moveList[i], i === highlightIdx));
    }
    currentStep = step;
    saveHistory();
    updateMoveButtons();
}
function prevMove() {
    if (moveList.length === 0 || currentStep <= 1) {
        showCustomModal('已经到第一步');
        return;
    }
    restoreToStep(currentStep - 1);
    updateMoveButtons();
}
function nextMove() {
    if (moveList.length === 0 || currentStep >= moveList.length) {
        showCustomModal('已经是最后一步');
        return;
    }
    restoreToStep(currentStep + 1);
    updateMoveButtons();
}
function prevChess() { showCustomModal('功能正在开发'); }
function nextChess() { showCustomModal('功能正在开发'); } 

// ========= 图片上传，识别，Ai 推荐=============================

// 1. 打开/关闭模态框
document.getElementById('uploadImageBtn').onclick = function() {
    document.getElementById('uploadModal').style.display = 'flex';
    resetFileInput();
};
document.getElementById('uploadModalCancel').onclick = function() {
    document.getElementById('uploadModal').style.display = 'none';
};

// 2. 文件选择/拖拽/粘贴
const imageInput = document.getElementById('imageInput');
const uploadArea = document.getElementById('uploadArea');
const previewImg = document.getElementById('previewImg');
const resetFileBtn = document.getElementById('resetFileBtn');
const uploadTip = document.getElementById('uploadTip');
let selectedFile = null;

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

uploadArea.onclick = () => imageInput.click();
imageInput.onchange = handleFileSelect;

uploadArea.ondragover = e => {
    e.preventDefault();
    uploadArea.classList.add('dragover');
};
uploadArea.ondragleave = e => {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
};
uploadArea.ondrop = e => {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
        imageInput.files = e.dataTransfer.files;
        handleFileSelect();
    }
};
document.addEventListener('paste', function(e) {
    if (document.getElementById('uploadModal').style.display !== 'none') {
        const items = (e.clipboardData || window.clipboardData).items;
        for (let item of items) {
            if (item.type.indexOf('image') !== -1) {
                const file = item.getAsFile();
                imageInput.files = new DataTransfer().files;
                const dt = new DataTransfer();
                dt.items.add(file);
                imageInput.files = dt.files;
                handleFileSelect();
                break;
            }
        }
    }
});

function handleFileSelect() {
    const file = imageInput.files[0];
    if (!file) return;
    selectedFile = file;
    const reader = new FileReader();
    reader.onload = function(e) {
        previewImg.src = e.target.result;
        previewImg.style.display = 'block';
        resetFileBtn.style.display = 'inline-block';
        uploadTip.style.display = 'none';
    };
    reader.readAsDataURL(file);
}
resetFileBtn.onclick = resetFileInput;
function resetFileInput() {
    imageInput.value = '';
    previewImg.src = '';
    previewImg.style.display = 'none';
    resetFileBtn.style.display = 'none';
    uploadTip.style.display = 'block';
    selectedFile = null;
}

// 3. 分析按钮
document.getElementById('analyzeBtn').onclick = function() {
    if (!selectedFile) {
        showCustomModal('请先上传图片');
        return;
    }
    analyzeImage(selectedFile);
};

// 4. analyzeImage 实现
function analyzeImage(file) {
    showLoading(true);
    const formData = new FormData();
    formData.append('image', file);
    // 可根据后端API调整参数
    fetch('/api/upload', {
        method: 'POST',
        body: formData
    })
    .then(resp => resp.json())
    .then(data => {
        console.log('analyzeImage',data)
        result = data.result
        showLoading(false)
        if (result) {
            renderAIRecommend(result);
            console.log('renderAIRecommend')
            if (result.fen) {
                setFEN(result.fen); // 你的主棋盘渲染函数
            }
            resetChess()
        }
        document.getElementById('uploadModal').style.display = 'none';
    })
    .catch(() => {
        showLoading(false)
        showCustomModal('图片识别失败，请重试');
    });
}

// 5. 渲染AI推荐到#ai-move
function renderAIRecommend(aiMove) {
    // aiMove建议为对象: { zh: '炮二平五', uci: 'c2e2', fen: 'xxx' }
    console.log('aiMove',aiMove)
    let html = '<b>AI推荐：</b>';
    const { fen, chinese_move,move,is_move } = aiMove;
    const nextMoveCard = document.getElementById('nextMoveCard');
    const nextMoveContent = document.getElementById('nextMoveContent');
    document.getElementById('ai-move').style.display='block'
    let color = '#212529'
    if(is_move === 'w'){
        color = '#dc3545'
    }
    if (nextMoveCard && nextMoveContent) {
        nextMoveContent.innerHTML = `
            <p class="text-muted mb-2" style="font-size: 0.9rem;">AI 建议</p>
            <div style="font-size: 2.2rem; font-weight: bold; color: ${color};">${chinese_move}(${move})</div>
            <div style="font-family: 'Courier New', Courier, monospace; color: #6c757d; margin-top: 0.5rem;">${fen}</div>
        `;
        nextMoveCard.classList.remove('d-none');
        nextMoveCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
    } else {
        console.error("UI elements 'nextMoveCard' or 'nextMoveContent' not found.");
    }
}