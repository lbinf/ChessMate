// 主题与规则配置

// ====== cellSize比例主题方案 ======
const THEME_LEVELS = 16;
let themeLevel = 16; // 默认等级16

// 比例参数配置 - 所有尺寸参数都以cellSize为基准的比例
const themeRatios = {
    cellSize: 1,
    boardPadding: 0.7,
    boardBorderWidth: 0.067,
    boardLineWidth: 0.027,
    coordFontSize: 0.21,
    pieceFontSize: 0.53,
    riverFontSize: 0.37,
    coordOuterMargin: 0.2,
    coordToBoardGap: 0.03,
    coordToBoardGapBottom: -0.067,
    coordMarginTop: 0,
    coordMarginBottom: 0.027,
    pieceRadius: 0.45,
    pieceStrokeWidth: 0.013,
    highlightWidth: 0.04,
    hoverWidth: 0.027,
    lMarkGap: 0.12,
    lMarkLength: 0.18,
    lMarkWidth: 0.04,
    riverTextGap: 0.12,
    riverTextLength: 0.24
};

const themes = {
    default: {
        boardBg: "#f5deb3",
        boardLineColor: "#5a3c20",
        boardBorderColor: "#5a3c20",
        pieceRedBg: "#D32F2F",
        pieceBlackBg: "#333333",
        pieceTextColor: "#fff",
        highlightColor: "#007bff",
        hoverColor: "#ff9800",
        statusBarBg: "#eee",
        statusBarColor: "#333",
        coordColor: '#b0a080',
        lMarkColor: "#7a5b2b"
    },
    dark: {
        boardBg: "#222",
        boardLineColor: "#bbb",
        boardBorderColor: "#fff",
        pieceRedBg: "#e53935",
        pieceBlackBg: "#222",
        pieceTextColor: "#fff",
        highlightColor: "#ffeb3b",
        hoverColor: "#ff9800",
        statusBarBg: "#222",
        statusBarColor: "#fff",
        coordColor: '#888',
        lMarkColor: "#7a5b2b"
    }
};

function getScaledTheme(baseTheme) {
    const cellSize = 3 * themeLevel;
    const scaled = { ...baseTheme };
    scaled.cellSize = cellSize;
    scaled.boardPadding = cellSize * themeRatios.boardPadding;
    scaled.boardBorderWidth = cellSize * themeRatios.boardBorderWidth;
    scaled.boardLineWidth = cellSize * themeRatios.boardLineWidth;
    scaled.coordFontSize = cellSize * themeRatios.coordFontSize;
    scaled.pieceFontSize = cellSize * themeRatios.pieceFontSize;
    scaled.coordOuterMargin = cellSize * themeRatios.coordOuterMargin;
    scaled.coordToBoardGap = cellSize * themeRatios.coordToBoardGap;
    scaled.coordToBoardGapBottom = cellSize * themeRatios.coordToBoardGapBottom;
    scaled.coordMarginTop = cellSize * themeRatios.coordMarginTop;
    scaled.coordMarginBottom = cellSize * themeRatios.coordMarginBottom;
    scaled.pieceRadiusRatio = themeRatios.pieceRadius;
    scaled.highlightWidth = cellSize * themeRatios.highlightWidth;
    scaled.hoverWidth = cellSize * themeRatios.hoverWidth;
    scaled.lMarkGap = cellSize * themeRatios.lMarkGap;
    scaled.lMarkLength = cellSize * themeRatios.lMarkLength;
    scaled.lMarkWidth = cellSize * themeRatios.lMarkWidth;
    scaled.reactPadding = themeLevel <= 5 ? 4 : themeLevel >= 14 ? 8 : 4 + Math.floor((themeLevel - 5) / (14 - 5) * 4)
    scaled.pieceFont = `bold ${scaled.pieceFontSize}px 'Microsoft YaHei', '微软雅黑', Arial, sans-serif`;
    const riverFontSize = cellSize * themeRatios.riverFontSize;
    scaled.riverText = [
        { text: "楚河", x: 2, y: 4.5, color: "#bfa16b", font: `bold ${riverFontSize}px KaiTi, 'Microsoft YaHei', serif`, alpha: 0.5 },
        { text: "汉界", x: 6, y: 4.5, color: "#bfa16b", font: `bold ${riverFontSize}px KaiTi, 'Microsoft YaHei', serif`, alpha: 0.5 },
        { text: "泡泡象棋", x: 4, y: 4.5, color: "#bfa16b", font: `bold ${riverFontSize * 0.8}px KaiTi, 'Microsoft YaHei', serif`, alpha: 0.4 }
    ];
    return scaled;
}

// 棋子与FEN映射
const pieceToChar = {
    'R_车': 'R', 'R_马': 'N', 'R_相': 'B', 'R_仕': 'A', 'R_帅': 'K', 'R_炮': 'C', 'R_兵': 'P',
    'B_车': 'r', 'B_马': 'n', 'B_象': 'b', 'B_士': 'a', 'B_将': 'k', 'B_炮': 'c', 'B_卒': 'p'
};
const charToPiece = {};
Object.entries(pieceToChar).forEach(([k, v]) => { charToPiece[v] = k; });
const pieceCharMap = {
    'R_帅': '帅', 'R_仕': '仕', 'R_相': '相', 'R_车': '车', 'R_马': '马', 'R_炮': '炮', 'R_兵': '兵',
    'B_将': '将', 'B_士': '士', 'B_象': '象', 'B_车': '车', 'B_马': '马', 'B_炮': '炮', 'B_卒': '卒'
};
const fileMap = {a:0, b:1, c:2, d:3, e:4, f:5, g:6, h:7, i:8};

// 走棋规则相关
function isLegalMove(board, from, to) {
    const piece = board[from.row][from.col];
    const target = board[to.row][to.col];
    if (!piece) return false;
    if (target && target[0] === piece[0]) return false;
    // 兵/卒规则
    if (piece === 'R_兵' || piece === 'B_卒') {
        const isRed = piece === 'R_兵';
        const fx = from.col, fy = from.row, tx = to.col, ty = to.row;
        if (isRed) {
            if (fx < 5) {
                if (tx === fx && ty > fy) return true;
            } else {
                if (ty > fy && tx === fx) return true;
                if (ty === fy && Math.abs(tx - fx) === 1) return true;
            }
        } else {
            if (fx > 4) {
                if (tx === fx && ty < fy) return true;
            } else {
                if (ty < fy && tx === fx) return true;
                if (ty === fy && Math.abs(tx - fx) === 1) return true;
            }
        }
        return false;
    }
    return true;
}

// FEN解析
function parseXiangqiFEN(fen) {
    const pieceMap = {
        r: 'B_车', n: 'B_马', b: 'B_象', a: 'B_士', k: 'B_将', c: 'B_炮', p: 'B_卒',
        R: 'R_车', N: 'R_马', B: 'R_相', A: 'R_仕', K: 'R_帅', C: 'R_炮', P: 'R_兵'
    };
    const [boardPart, turnPart] = fen.split(' ');
    const rows = boardPart.split('/');
    const board = [];
    for (let row = 0; row < 10; row++) {
        const fenRow = rows[9 - row];
        const boardRow = [];
        let col = 0;
        for (const ch of fenRow) {
            if (/\d/.test(ch)) {
                for (let i = 0; i < parseInt(ch); i++) boardRow.push('');
                col += parseInt(ch);
            } else {
                boardRow.push(pieceMap[ch] || '');
                col++;
            }
        }
        board[row] = boardRow;
    }
    return {board, turn: (turnPart || 'w').trim()};
}

// 导出到全局
window.THEME_LEVELS = THEME_LEVELS;
window.themeLevel = themeLevel;
window.themeRatios = themeRatios;
window.themes = themes;
window.getScaledTheme = getScaledTheme;
window.pieceToChar = pieceToChar;
window.charToPiece = charToPiece;
window.pieceCharMap = pieceCharMap;
window.fileMap = fileMap;
window.isLegalMove = isLegalMove;
window.parseXiangqiFEN = parseXiangqiFEN; 