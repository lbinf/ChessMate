import time
import json
import subprocess
import os
from app.logging_config import logger
import logging
from app.logging_handlers import ShutdownHandler
import threading

class Engine:
    def __init__(self, pikafish_path=None, params_file=None):
        engine_dir = os.path.dirname(os.path.abspath(__file__))
        self.pikafish_path = pikafish_path or os.path.join(engine_dir, '..', 'Pikafish', 'src', 'pikafish')
        self.params_file = params_file or os.path.join(engine_dir, '..', 'json', 'params.json')
        self.pikafish = None
        self.engine_available = False
        self.params = self._load_parameters()
        self._shutdown_handler = None
        self.last_analysis_lines = []
        self._init_engine()

    def _load_parameters(self):
        defaults = {"goParam": "depth", "depth": "20", "movetime": "3000"}
        try:
            with open(self.params_file, 'r') as f:
                loaded_params = json.load(f)
            defaults['goParam'] = loaded_params.get('goParam', loaded_params.get('current', 'depth'))
            value_dict = loaded_params.get('value', {})
            defaults['depth'] = loaded_params.get('depth', value_dict.get('depth', '20'))
            defaults['movetime'] = loaded_params.get('movetime', value_dict.get('movetime', '3000'))
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        self.params = defaults
        self.save_parameters()
        return self.params

    def save_parameters(self):
        with open(self.params_file, 'w') as f:
            json.dump(self.params, f, indent=4)

    def _init_engine(self):
        try:
            if not os.path.exists(self.pikafish_path):
                logger.warning(f"AI引擎文件不存在: {self.pikafish_path}")
                return
            if not os.access(self.pikafish_path, os.X_OK):
                logger.warning(f"AI引擎文件不可执行: {self.pikafish_path}")
                return
            self.pikafish = subprocess.Popen(
                [self.pikafish_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            time.sleep(1)
            self.uci()
            self.set_option('Threads', '2')
            self.set_option('Hash', '256')
            if self.isready() == 'readyok':
                self.engine_available = True
                logger.info("AI引擎初始化成功")
            else:
                raise Exception("Engine not ready after initialization")
        except Exception as e:
            logger.error(f"AI引擎初始化失败: {e}")
            self.engine_available = False
            if self.pikafish:
                self.pikafish.terminate()
                self.pikafish = None

    def get_best_move(self, fen, side):
        logger.info(f"[Engine] get_best_move: FEN={fen}, side={side}, params={self.params}")
        if not self.engine_available:
            logger.warning("AI引擎不可用，返回模拟结果")
            return "a1a2", '',fen + ' ' + side
        try:
            fen_string = fen + ' ' + side
            param = self.params.get('goParam', 'depth')
            value = self.params.get(param, '15')
            lines, best_move = self.go(fen_string, param, str(value))
            logger.info(f"[Engine] lines: {lines},best_move:{best_move}")
            line = ''
            if not lines:
                logger.warning("[Engine] No lines received from engine (timeout).")
                best_move_code = "a1a2"
            else:
                if best_move:
                    start_index = best_move.find('bestmove')
                    if start_index != -1:
                        best_move_code = best_move[start_index + 9:start_index + 13]
                    else:
                        best_move_code = "a1a2"
                else:
                    best_move_code = "a1a2"

                if len(lines)>=2:
                    line = lines[-2]
                elif len(lines)==1:
                    line = lines[0]

            logger.info(f"[Engine] Final best move: {best_move_code}")
            return best_move_code,line, fen_string
        except Exception as e:
            logger.error(f"获取最佳走法时出错: {e}")
            return "a1a2", fen + ' ' + ('w' if side else 'b')

    def send_command(self, cmd, interval, keyword):
        if self.pikafish is None:
            return []
        try:
            self.pikafish.stdin.write(f'{cmd}\n')
            self.pikafish.stdin.flush()
            lines = []
            start_time = time.time()
            while True:
                output = self.pikafish.stdout.readline().strip()
                if (time.time() - start_time > interval):
                    break
                if output:
                    lines.append(output)
                    if keyword in output:
                        break
            return lines
        except Exception as e:
            logger.error(f"发送命令时出错: {e}")
            return []

    def uci(self):
        if self.pikafish is None:
            return []
        try:
            self.pikafish.stdin.write('uci\n')
            self.pikafish.stdin.flush()
            lines = []
            start_time = time.time()
            while True:
                output = self.pikafish.stdout.readline().strip()
                if (time.time() - start_time > 1):
                    break
                if output:
                    lines.append(output)
                    if 'uciok' in output:
                        break
            return lines
        except Exception as e:
            logger.error(f"UCI命令出错: {e}")
            return []

    def isready(self):
        if self.pikafish is None:
            return ""
        try:
            self.pikafish.stdin.write('isready\n')
            self.pikafish.stdin.flush()
            start_time = time.time()
            while True:
                output = self.pikafish.stdout.readline().strip()
                if time.time() - start_time > 2:
                    logger.warning("[Engine] isready timeout")
                    return ""
                if 'readyok' in output:
                    return "readyok"
        except Exception as e:
            logger.error(f"isready命令出错: {e}")
            return ""

    def set_option(self, name, value):
        if self.pikafish is None:
            return
        try:
            cmd = f'setoption name {name} value {value}'
            self.pikafish.stdin.write(f'{cmd}\n')
            self.pikafish.stdin.flush()
            time.sleep(0.1)
        except Exception as e:
            logger.error(f"setoption命令出错: {e}")

    def ucinewgame(self):
        if self.pikafish is None:
            return ""
        try:
            self.pikafish.stdin.write('ucinewgame\n')
            self.pikafish.stdin.flush()
            return self.isready()
        except Exception as e:
            logger.error(f"ucinewgame命令出错: {e}")
            return ""

    def go(self, fen_string, param, value):
        self.last_analysis_lines = []
        if self.pikafish is None:
            return [], "bestmove a1a2"
        try:
            start_fen_board = "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR"
            if fen_string.startswith(start_fen_board):
                logger.info("[Engine] Detected start position, sending ucinewgame and position startpos.")
                self.ucinewgame()
                pos_command = "position startpos\n"
            else:
                pos_command = "position fen " + fen_string + "\n"
            logger.info(f"[Engine] > Sending command: {pos_command.strip()}")
            self.pikafish.stdin.write(pos_command)
            go_command = "go " + param + " " + value + "\n"
            logger.info(f"[Engine] > Sending command: {go_command.strip()}")
            self.pikafish.stdin.write(go_command)
            self.pikafish.stdin.flush()
            lines, best_move = self._read_output_with_timeout(50)
            return lines, best_move
        except Exception as e:
            logger.error(f"go命令出错: {e}")
            return [], "bestmove a1a2"

    def _read_output_with_timeout(self, timeout=1):
        if self.pikafish is None:
            return [], "bestmove a1a2"
        try:
            lines = []
            best_move = ''
            start_time = time.time()
            while True:
                output = self.pikafish.stdout.readline().strip()
                if time.time() - start_time > timeout:
                    logger.warning("[Engine] < Read timeout reached.")
                    break
                if output:
                    self.last_analysis_lines.append(output)
                    lines.append(output)
                    if "bestmove" in output:
                        best_move = output
                        break
            return lines, best_move
        except Exception as e:
            logger.error(f"读取输出时出错: {e}")
            return [], "bestmove a1a2"

    def get_last_analysis_lines(self):
        """Returns the raw analysis lines from the last 'go' command."""
        return self.last_analysis_lines

    def _get_shutdown_handler(self):
        """
        获取或创建关闭日志处理器
        """
        if self._shutdown_handler is None:
            self._shutdown_handler = ShutdownHandler()
            root_logger = logging.getLogger()
            root_logger.addHandler(self._shutdown_handler)
        return self._shutdown_handler

    def close(self):
        """
        关闭引擎实例
        """
        try:
            # 执行必要的清理操作
            self._cleanup()
            
            # 使用特殊的处理器记录关闭消息
            shutdown_handler = self._get_shutdown_handler()
            shutdown_logger = logging.getLogger("engine.shutdown")
            shutdown_logger.addHandler(shutdown_handler)
            shutdown_logger.propagate = False
            shutdown_logger.info("AI engine shut down.")
            
        except Exception as e:
            # 同样使用特殊处理器记录错误
            shutdown_logger = logging.getLogger("engine.shutdown")
            shutdown_logger.error(f"Error during engine shutdown: {e}")
        finally:
            self._set_running(False)
            if self._shutdown_handler:
                try:
                    self._shutdown_handler.close()
                except:
                    pass

    def _cleanup(self):
        """
        执行引擎关闭时的清理工作
        """
        if self.pikafish:
            try:
                self.pikafish.stdin.write('quit\n')
                self.pikafish.stdin.flush()
            except (IOError, BrokenPipeError) as e:
                logger.debug(f"Error writing to engine pipe: {e}")
            
            try:
                self.pikafish.terminate()
                self.pikafish.wait(timeout=2)
            except Exception as e:
                logger.warning(f"Error terminating engine process: {e}")
            finally:
                self.pikafish = None

    @property
    def _is_running(self):
        return self.engine_available

    def _set_running(self, value):
        self.engine_available = value 