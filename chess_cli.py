#!/usr/bin/env python3
"""
中国象棋命令行工具启动脚本
使用方法：
    python chess_cli.py          # 运行演示模式
    python chess_cli.py --cli    # 运行交互式命令行
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

def main():
    if len(sys.argv) > 1 and sys.argv[1] == '--cli':
        # 运行交互式命令行
        from app.chess.chess_cli import run_command_line
        run_command_line()
    else:
        # 运行演示模式
        from app.chess.chess_cli import ChessBoard
        try:
            board = ChessBoard()
            print("=== 中国象棋引擎演示 ===")
            print("--- 初始棋盘 (红上黑下) ---")
            print(board)
            print(f"初始FEN: {board.to_fen()}")
            
            print("\n=== 演示移动 ===")
            print(f"当前轮到: {'红方' if board.player_to_move == 'red' else '黑方'} 行动")
            
            # 演示几个移动
            moves = [
                ((7, 2), (4, 2), "炮二平五"),
                ((7, 7), (4, 7), "炮8平5"),
                ((7, 9), (6, 7), "马8进7"),
                ((6, 0), (8, 2), "相三进一"),
                ((8, 9), (8, 8), "车9进1")
            ]
            
            for i, (from_pos, to_pos, desc) in enumerate(moves, 1):
                print(f"\n--- 第{i}步移动: {desc} ---")
                piece = board.pieces.get(from_pos)
                if piece:
                    color_str = "红方" if piece.color == 'red' else "黑方"
                    notation = board.move_piece(from_pos, to_pos)
                    print(f"移动: {color_str} {piece.name}({from_pos}) -> {to_pos} ({notation})")
                    print(board)
                    print(f"FEN: {board.to_fen()}")
                else:
                    print(f"错误: 位置 {from_pos} 没有棋子")
            
            print("\n=== 演示完成 ===")
            print("要启动交互式命令行，请运行: python chess_cli.py --cli")
            
        except Exception as e:
            import traceback
            print(f"\n发生错误: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    main() 