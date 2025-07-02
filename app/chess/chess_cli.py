import sys
import os
import readline
import atexit

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.chess.board import ChessBoard, ChessPiece

def run_command_line():
    """运行命令行界面"""
    # 设置readline以支持历史记录和编辑
    histfile = os.path.join(os.path.expanduser("~"), ".chess_history")
    try:
        readline.read_history_file(histfile)
        # 设置历史记录大小
        readline.set_history_length(1000)
    except FileNotFoundError:
        pass
    
    # 注册退出时保存历史记录
    atexit.register(readline.write_history_file, histfile)
    
    # 设置readline的编辑模式
    readline.parse_and_bind("tab: complete")
    
    game = ChessBoard()
    print("中国象棋引擎 - 命令行界面")
    print("输入 'help' 查看帮助")
    print()
    
    while True:
        try:
            # 使用input()获取用户输入，现在支持历史记录和编辑
            command = input("请输入命令: ").strip()
            
            if not command:
                continue
                
            if command == "quit":
                print("再见!")
                break
            elif command == "help":
                print("可用命令:")
                print("  new - 开始新游戏")
                print("  quit - 退出程序")
                print("  help - 显示帮助")
                print("  fen <fen_string> - 从FEN字符串加载棋盘状态")
                print("  move <x y x y> - 使用原始坐标移动棋子")
                print("  state - 显示当前棋盘和FEN字符串")
                print("  pos <x> <y> - 显示指定坐标的棋子")
                print("  notation <chinese_notation> - 解析并执行中文记谱法")
                print("  chinese <chinese_notation> - 改进的中文记谱法解析")
                print("  mv <ucci_move> - 解析UCCI记谱法 (如: h2e2)")
                print("  mtc <move> - 将着法转换为坐标移动")
                print("  ctm <start_col> <start_row> <end_col> <end_row> - 将坐标移动转换为着法")
                print("  cc <engine_move> - 将引擎着法转换为中文描述")
                print()
            elif command == "new":
                game = ChessBoard()
                print("新游戏已开始")
                print(game)
                print()
            elif command.startswith("fen "):
                fen_str = command.split(" ", 1)[1]
                try:
                    game = ChessBoard(fen_str)
                    print("棋盘状态已加载")
                    print(game)
                    print()
                except Exception as e:
                    print(f"加载FEN失败: {e}")
                    print()
            elif command.startswith("move "):
                try:
                    parts = command.split()[1:]
                    if len(parts) == 4:
                        from_x, from_y, to_x, to_y = map(int, parts)
                        notation = game.move_piece((from_x, from_y), (to_x, to_y))
                        print(f"移动: {notation}")
                        print(game)
                        print()
                    else:
                        print("正确格式: move <from_x> <from_y> <to_x> <to_y>")
                        print()
                except (ValueError, IndexError) as e:
                    print(f"移动失败: {e}")
                    print("正确格式: move <from_x> <from_y> <to_x> <to_y>")
                    print()
            elif command.startswith("state"):
                print(game)
                print("FEN:", game.to_fen())
                print()
            elif command.startswith("pos "):
                try:
                    parts = command.split()[1:]
                    if len(parts) == 2:
                        x, y = map(int, parts)
                        piece = game.pieces.get((x, y))
                        if piece:
                            print(f"位置 ({x}, {y}): {piece.name} ({piece.color})")
                        else:
                            print(f"位置 ({x}, {y}): 空")
                    else:
                        print("正确格式: pos <x> <y>")
                    print()
                except (ValueError, IndexError):
                    print("正确格式: pos <x> <y>")
                    print()
            elif command.startswith("notation "):
                notation = command.split(" ", 1)[1]
                try:
                    from_pos, to_pos = game.parse_chinese_notation(notation)
                    from_x, from_y = from_pos
                    to_x, to_y = to_pos
                    
                    print(f"解析着法: {notation}")
                    print(f"移动坐标: ({from_x}, {from_y}) -> ({to_x}, {to_y})")
                    
                    # 检查起始位置是否有棋子
                    if from_pos not in game.pieces:
                        print(f"错误: 位置 ({from_x}, {from_y}) 没有棋子")
                        print()
                        continue
                    
                    piece = game.pieces[from_pos]
                    color_str = "红方" if piece.color == 'red' else "黑方"
                    move_desc = f"{piece.name}({from_x}, {from_y}) -> ({to_x}, {to_y})"
                    
                    # 移动棋子并获取记谱法
                    notation_result = game.move_piece(from_pos, to_pos)
                    
                    print(f"移动: {color_str} {move_desc} ({notation_result})")
                    print(game)
                    print(f"移动后FEN: {game.to_fen()}")
                    print()
                    
                except Exception as e:
                    print(f"着法解析错误: {e}")
                    print("着法示例:")
                    print("  notation 马8进7")
                    print("  notation 炮二平五")
                    print("  notation 车9进1")
                    print()
            elif command.startswith("chinese "):
                notation = command.split(" ", 1)[1]
                game.handle_chinese_notation(notation)
                print()
            elif command.startswith("mv "):
                ucci_move = command.split(" ", 1)[1].strip()
                if ucci_move:
                    game.handle_ucci_move(ucci_move)
                else:
                    print("Please provide a UCCI move, e.g., 'mv h2e2'.")
                print()
            elif command.startswith("mtc "):
                move = command.split(" ", 1)[1].strip()
                try:
                    coords = game.move_to_coords(move)
                    print(f"着法 {move} 转换为坐标: {coords}")
                except Exception as e:
                    print(f"转换失败: {e}")
                print()
            elif command.startswith("ctm "):
                parts = command.split()
                if len(parts) == 5:
                    try:
                        start_col = int(parts[1])
                        start_row = int(parts[2])
                        end_col = int(parts[3])
                        end_row = int(parts[4])
                        move = game.coords_to_move(start_col, start_row, end_col, end_row)
                        print(f"坐标 ({start_col},{start_row}) -> ({end_col},{end_row}) 转换为着法: {move}")
                    except Exception as e:
                        print(f"转换失败: {e}")
                else:
                    print("用法: ctm <start_col> <start_row> <end_col> <end_row>")
                print()
            elif command.startswith("cc "):
                engine_move = command.split(" ", 1)[1].strip()
                try:
                    chinese_notation = game.engine_move_to_chinese_notation(engine_move)
                    print(f"引擎着法 '{engine_move}' 的中文描述是: {chinese_notation}")
                except Exception as e:
                    print(f"转换失败: {e}")
                print()
            else:
                print("未知命令，输入 'help' 查看帮助")
                print()
                
        except KeyboardInterrupt:
            print("\n使用 'quit' 命令退出程序")
            print()
        except EOFError:
            print("\n再见!")
            break
        except Exception as e:
            print(f"发生错误: {e}")
            print()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--cli':
        run_command_line()
    else:
        # 原有的演示代码
        try:
            board = ChessBoard()
            print("--- 初始棋盘 (红上黑下) ---")
            print(board)
            print(f"初始FEN: {board.to_fen()}")
            # 初始化后的 FEN 应该是 rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w
            
            print("\n--- 第一次移动 ---")
            print(f"当前轮到: {'红方' if board.player_to_move == 'red' else '黑方'} 行动")
            # 炮二平五
            from_pos = (7, 2)
            to_pos = (4, 2)

            # 获取棋子信息用于打印
            piece = board.pieces.get(from_pos)
            if not piece:
                raise ValueError(f"位置 {from_pos} 没有棋子")
            
            color_str = "红方" if piece.color == 'red' else "黑方"
            move_desc = f"{piece.name}{from_pos} -> {to_pos}"

            # 移动棋子并获取记谱法
            notation = board.move_piece(from_pos, to_pos)
            
            print(f"移动: {color_str} {move_desc} ({notation})")
            print(board)
            
            print(f"移动后FEN: {board.to_fen()}")
            # 移动后的 FEN 应该是 rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C2C4/9/RNBAKABNR b

            print("\n--- 第二次移动 ---")
            print(f"当前轮到: {'红方' if board.player_to_move == 'red' else '黑方'} 行动")
            # 炮8平5 (7,7)->(4,7)
            from_pos = (7, 7)
            to_pos = (4, 7)
            
             # 获取棋子信息用于打印
            piece = board.pieces.get(from_pos)
            if not piece:
                raise ValueError(f"位置 {from_pos} 没有棋子")
            
            color_str = "红方" if piece.color == 'red' else "黑方"
            move_desc = f"{piece.name}{from_pos} -> {to_pos}"

            notation = board.move_piece(from_pos, to_pos)

            print(f"移动: {color_str} {move_desc} ({notation})")
            print(board)
          
            print(f"移动后FEN: {board.to_fen()}")
            # 移动后的 FEN 应该是 rnbakabnr/9/1c2c4/p1p1p1p1p/9/9/P1P1P1P1P/1C2C4/9/RNBAKABNR w
            print(f"移动后FEN: {board.to_fen()}")

            #黑方 马8进7
            from_pos = (7, 9)
            to_pos = (6, 7)
            print(f"当前轮到: {'红方' if board.player_to_move == 'red' else '黑方'} 行动")

             # 获取棋子信息用于打印
            piece = board.pieces.get(from_pos)
            if not piece:
                raise ValueError(f"位置 {from_pos} 没有棋子")
            
            color_str = "红方" if piece.color == 'red' else "黑方"
            move_desc = f"{piece.name}{from_pos} -> {to_pos}"

             # 移动棋子并获取记谱法
            notation = board.move_piece(from_pos, to_pos)
            
            print(f"移动: {color_str} {move_desc} ({notation})")
            print(board)
           
            print(f"移动后FEN: {board.to_fen()}")

            #红方 相三进一
            from_pos = (6, 0)
            to_pos = (8, 2)
            print(f"当前轮到: {'红方' if board.player_to_move == 'red' else '黑方'} 行动")

             # 获取棋子信息用于打印
            piece = board.pieces.get(from_pos)
            if not piece:
                raise ValueError(f"位置 {from_pos} 没有棋子")
            
            color_str = "红方" if piece.color == 'red' else "黑方"
            move_desc = f"{piece.name}{from_pos} -> {to_pos}"

             # 移动棋子并获取记谱法
            notation = board.move_piece(from_pos, to_pos)
            
            print(f"移动: {color_str} {move_desc} ({notation})")
            print(board)
            
            print(f"移动后FEN: {board.to_fen()}")

            #黑方 车9进1
            from_pos = (8, 9)
            to_pos = (8, 8)
            print(f"当前轮到: {'红方' if board.player_to_move == 'red' else '黑方'} 行动")

             # 获取棋子信息用于打印
            piece = board.pieces.get(from_pos)
            if not piece:
                raise ValueError(f"位置 {from_pos} 没有棋子")
            
            color_str = "红方" if piece.color == 'red' else "黑方"
            move_desc = f"{piece.name}{from_pos} -> {to_pos}"

             # 移动棋子并获取记谱法
            notation = board.move_piece(from_pos, to_pos)
            
            print(f"移动: {color_str} {move_desc} ({notation})")
            print(board)
            
            print(f"移动后FEN: {board.to_fen()}")

        except Exception as e:
            import traceback
            print("\nAn error occurred:")
            traceback.print_exc()