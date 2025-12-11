#!/usr/bin/env python3
"""
SSH 服務器 - Rich 美化版本
使用 Rich 但避免複雜排版，適用於 SSH 終端
"""

import os
import sys
import socket
import threading
import paramiko
import time
from pathlib import Path

# 添加當前目錄到 Python 路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

REPO_ROOT = Path(parent_dir).resolve()
DEFAULT_UPLOAD_DIR = REPO_ROOT / "upload_files"

class SSHShell(paramiko.ServerInterface):
    """SSH Shell 處理器 - 純文字版"""
    
    def __init__(self, username, client_address, fastapi_url="http://localhost:8000"):
        self.username = username
        self.client_address = client_address
        self.fastapi_url = fastapi_url
        self.current_path = "C:\\"
        self.channel = None
        self.upload_dir = DEFAULT_UPLOAD_DIR
        self._exit_requested = False
    
    def check_auth_password(self, username, password):
        """密碼認證"""
        users = {
            "admin": "password123",
            "user": "userpass", 
            "guest": "guest",
            "demo": "demo123"
        }
        
        if username in users and users[username] == password:
            self.username = username
            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED
    
    def check_channel_request(self, kind, chanid):
        """檢查通道請求"""
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED
    
    def check_channel_shell_request(self, channel):
        """檢查 shell 請求"""
        self.channel = channel
        return True
    
    def check_channel_pty_request(self, channel, term, width, height, pixelwidth, pixelheight, modes):
        """檢查 PTY 請求"""
        return True
    
    def send_prompt(self):
        """發送命令提示符"""
        if not self.channel:
            return
        prompt = self.username + "@fileserver:" + self.current_path + "$ "
        try:
            # 先換行再顯示提示符，避免與上一行黏在一起
            self.channel.send(b"\r\n")
            self.channel.send(prompt.encode('ascii', errors='ignore'))
        except:
            pass
    
    def safe_send(self, message):
        """安全地發送訊息 - 清理所有隱藏字符"""
        if self.channel and not self.channel.closed:
            try:
                # 允許 ANSI 控制序列 (顏色/樣式)；僅規範換行為 CRLF
                text = str(message)
                text = text.replace('\r\n', '\n').replace('\r', '\n').replace('\n', '\r\n')
                # 直接以 UTF-8 發送，保留 ESC (\x1b) 等序列
                self.channel.send(text.encode('utf-8', errors='ignore'))
            except Exception as e:
                print(f"發送訊息失敗: {e}")
    
    def run_shell(self):
        """運行 shell 會話：持續自動執行 ClockMate，直到使用者於 ClockMate 內輸入 exit/quit。"""
        if not self.channel:
            print("錯誤: channel 未設置")
            return
        try:
            # 持續自動執行 ClockMate（llm 模式）
            while True:
                if self.channel is None or self.channel.closed:
                    break
                cont = self.run_clockmate('llm')
                if not cont:
                    # run_clockmate 已執行關閉（若是 exit）
                    return
        except Exception as e:
            print(f"SSH Shell 會話錯誤: {e}")
        finally:
            try:
                if self.channel and not self.channel.closed:
                    self.channel.close()
            except Exception:
                pass

    def process_command(self, command: str):
        """處理命令"""
        parts = command.split()
        if not parts:
            return
        
        cmd = parts[0].lower()
        
        try:
            if cmd == 'clockmate':
                # 支援參數: --mode/-m（預設 llm）
                import shlex
                mode = 'llm'
                try:
                    tokens = shlex.split(command)
                except Exception:
                    tokens = parts
                # 參數檢查與建議：擋下任何未知的 --參數
                recognized = {'--mode', '-m'}
                # 收集使用者輸入的長參數 (以 - 開頭)
                bad_params = []
                suggestions = []
                import difflib
                for t in tokens[1:]:
                    if t.startswith('-'):
                        # 若是 key=value 形式，拆 key
                        key = t.split('=')[0]
                        if key not in recognized:
                            bad_params.append(t)
                            # 給出最相近的建議
                            close = difflib.get_close_matches(key, list(recognized), n=1, cutoff=0.5)
                            if close:
                                suggestions.append(f"{t} → {close[0]}")
                            else:
                                suggestions.append(f"{t} (未知參數)")
                if bad_params:
                    msg_lines = ["❌ 未知參數:"] + [f"  - {bp}" for bp in bad_params]
                    if suggestions:
                        msg_lines.append("可能想輸入:")
                        msg_lines += [f"  - {s}" for s in suggestions]
                    msg_lines.append("請使用 'clockmate --mode llm' 或 'clockmate --mode manual'")
                    self.safe_send("\r\n" + "\r\n".join(msg_lines) + "\r\n")
                    return
                i = 1
                while i < len(tokens):
                    tok = tokens[i]
                    if tok in ('--mode', '-m') and i + 1 < len(tokens):
                        mode = tokens[i+1].lower()
                        i += 2
                        continue
                    i += 1

                # 僅接受 llm 或 manual
                if mode not in ('llm', 'manual'):
                    self.safe_send("mode 僅支援 'llm' 或 'manual'")
                    return
                self.run_clockmate(mode)
            elif cmd == 'clear':
                self.clear_screen()
            elif cmd in ['quit', 'exit']:
                self.show_goodbye()
                return
            else:
                error_text = f"未知命令: {cmd}\r\n"
                self.channel.send(error_text.encode('utf-8'))
                
        except Exception as e:
            error_text = f"命令執行錯誤: {str(e)}\r\n"
            self.channel.send(error_text.encode('utf-8'))

    def run_clockmate(self, mode: str = 'llm'):
        """在 SSH channel 中執行 ClockMate CLI，橋接 stdin/stdout。
        回傳 True 代表完成並可繼續，False 代表使用者要求離開。
        """
        from clockmate.main import run_llm_cli, set_output_stream, set_io_hooks

        class ChannelWriter:
            def __init__(self, shell_ref):
                self.shell_ref = shell_ref
                # 標記為非 plain，讓 Rich 啟用樣式渲染
                self.is_plain = False
            def write(self, s):
                if not s:
                    return
                try:
                    data = s.replace('\n', '\r\n') if isinstance(s, str) else s
                    self.shell_ref.channel.send(data.encode('utf-8') if isinstance(data, str) else data)
                except Exception:
                    pass
            def flush(self):
                pass
            def isatty(self):
                return True

        class ChannelReader:
            def __init__(self, channel):
                self.channel = channel
                self.buffer = b""
                # 使用位元組收集目前行內容，支援 UTF-8
                self._current_line_bytes = bytearray()
            def _fill(self):
                if self.channel.closed:
                    return False
                try:
                    chunk = self.channel.recv(1)
                    if not chunk:
                        return False
                    # 安全 echo：僅回顯可見字元與換行，忽略控制字元避免破壞介面
                    try:
                        b = chunk[0]
                        if chunk in (b"\r", b"\n"):
                            # Enter：視覺換行；內容由 readline() 取出
                            self.channel.send(b"\r\n")
                        elif b in (0x08, 0x7F):
                            # Backspace：只在有字元時刪除，不影響既有 UI
                            if self._current_line_bytes:
                                # 簡化處理：移除最後一個位元組
                                # （對多位元組 UTF-8，可能一次刪除半個字元，但實務上可接受）
                                self._current_line_bytes = self._current_line_bytes[:-1]
                                self.channel.send(b"\x08 \x08")
                        elif 32 <= b <= 126:
                            # 可見 ASCII：追加並顯示
                            self._current_line_bytes.extend(chunk)
                            self.channel.send(chunk)
                        elif b >= 128:
                            # 非 ASCII（可能為 UTF-8 多位元組）：直接回顯並累積位元組
                            self._current_line_bytes.extend(chunk)
                            self.channel.send(chunk)
                        else:
                            # 其他控制碼（如 ESC/方向鍵）忽略
                            pass
                    except Exception:
                        pass
                    self.buffer += chunk
                    return True
                except Exception:
                    return False
            def readline(self):
                line = b""
                while True:
                    nl_pos = self.buffer.find(b"\n")
                    cr_pos = self.buffer.find(b"\r")
                    pos_candidates = [p for p in [nl_pos, cr_pos] if p != -1]
                    if pos_candidates:
                        pos = min(pos_candidates)
                        # 使用目前行的位元組資料（已處理 Backspace），以 UTF-8 解碼
                        try:
                            line_text = self._current_line_bytes.decode('utf-8', errors='ignore')
                        except Exception:
                            line_text = ''.join(chr(b) for b in self._current_line_bytes)
                        rest = self.buffer[pos+1:]
                        if rest.startswith(b"\n") or rest.startswith(b"\r"):
                            rest = rest[1:]
                        self.buffer = rest
                        # 清空目前行緩衝
                        self._current_line_bytes.clear()
                        return line_text
                    if not self._fill():
                        line += self.buffer
                        self.buffer = b""
                        break
                return line.decode('utf-8', errors='ignore')
            def read(self, size=-1):
                if size == -1:
                    return self.readline()
                out = b""
                while len(out) < size:
                    if not self.buffer:
                        if not self._fill():
                            break
                    take = min(size - len(out), len(self.buffer))
                    out += self.buffer[:take]
                    self.buffer = self.buffer[take:]
                return out.decode('utf-8', errors='ignore')
            def isatty(self):
                return True

        class ExitRequested(Exception):
            pass

        # 暫時替換標準 IO
        original_stdin = sys.stdin
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        writer = ChannelWriter(self)
        reader = ChannelReader(self.channel)
        sys.stdin = reader
        sys.stdout = writer
        sys.stderr = writer
        set_output_stream(writer)

        # 提供簡化的輸入/確認掛勾，避免 Rich 的進階互動在 SSH 下出現 EOF
        def ssh_input(prompt_text: str, default_val=None) -> str:
            try:
                # 顯示提示
                try:
                    self.channel.send((prompt_text.replace('\n', '\r\n')).encode('utf-8'))
                except Exception:
                    pass
                # 讀取一整行
                line = sys.stdin.readline()
                if line is None:
                    return default_val or ""
                # 正規化：移除零寬度與格式控制字元、替換 NBSP、去除 CR/LF
                try:
                    import unicodedata
                    def _normalize_text(s: str) -> str:
                        s = s.replace('\r', '').replace('\n', '')
                        # 將 NBSP 轉成一般空白
                        s = s.replace('\u00A0', ' ')
                        # 移除 BOM 與零寬度/格式控制字元
                        remove_chars = {
                            '\ufeff',  # BOM / ZWNBSP
                            '\u200b', '\u200c', '\u200d',  # ZWSP, ZWNJ, ZWJ
                            '\u2060',  # WORD JOINER
                            '\u200e', '\u200f',  # LRM, RLM
                        }
                        for ch in remove_chars:
                            s = s.replace(ch, '')
                        # 移除其餘一般控制/格式字元
                        s = ''.join(c for c in s if unicodedata.category(c) not in ('Cf', 'Cc'))
                        return s
                    line = _normalize_text(line)
                except Exception:
                    line = line.rstrip('\r\n')
                if line.strip().lower() in ("exit", "quit"):
                    self._exit_requested = True
                    raise ExitRequested()
                return line if line != "" else (default_val or "")
            except Exception:
                # 若為主動離開，拋例外供上層處理
                raise

        def ssh_confirm(prompt_text: str, default: bool = True) -> bool:
            suffix = " [Y/n]: " if default else " [y/N]: "
            try:
                try:
                    self.channel.send((prompt_text + suffix).encode('utf-8'))
                except Exception:
                    pass
                ans = sys.stdin.readline()
                if not ans:
                    return default
                # 正規化輸入同 ssh_input
                try:
                    import unicodedata
                    def _normalize_text(s: str) -> str:
                        s = s.replace('\r', '').replace('\n', '')
                        s = s.replace('\u00A0', ' ')
                        remove_chars = {'\ufeff','\u200b','\u200c','\u200d','\u2060','\u200e','\u200f'}
                        for ch in remove_chars:
                            s = s.replace(ch, '')
                        s = ''.join(c for c in s if unicodedata.category(c) not in ('Cf', 'Cc'))
                        return s
                    ans = _normalize_text(ans)
                except Exception:
                    ans = ans.strip()
                ans = ans.strip().lower()
                if ans in ("exit", "quit"):
                    self._exit_requested = True
                    raise ExitRequested()
                if ans in ("y", "yes"):
                    return True
                if ans in ("n", "no"):
                    return False
                return default
            except Exception:
                raise

        set_io_hooks(input_func=ssh_input, confirm_func=ssh_confirm)

        try:
            run_llm_cli(mode=mode, output_stream=writer)
            return True
        except ExitRequested:
            # 使用者要求離開：直接關閉連線
            self.show_goodbye()
            return False
        except Exception as e:
            self.safe_send(f"ClockMate 執行失敗: {e}")
            # 發生錯誤時，仍允許下一輪重試
            return True
        finally:
            sys.stdin = original_stdin
            sys.stdout = original_stdout
            sys.stderr = original_stderr

    def show_goodbye(self):
        """顯示再見訊息"""
        goodbye_text = (
            "\r\n=============================\r\n"
            f"再見, {self.username}！\r\n"
            "感謝使用 Clockmate\r\n"
            "連接即將關閉...\r\n"
            "=============================\r\n\r\n"
        )
        
        self.channel.send(goodbye_text.encode('utf-8'))
        time.sleep(1)
        self.channel.close()

class SSHServer:
    """SSH 服務器"""
    
    def __init__(self, host="127.0.0.1", port=2222, fastapi_url="http://localhost:8000"):
        self.host = host
        self.port = port
        self.fastapi_url = fastapi_url
        self.server_key = None
        self.key_file = "ssh_host_key.pem"  # 金鑰檔案路徑
        self.load_or_generate_server_key()
    
    def load_or_generate_server_key(self):
        """載入或生成服務器金鑰"""
        try:
            # 嘗試載入現有的金鑰
            if os.path.exists(self.key_file):
                print(f"載入現有 SSH 金鑰: {self.key_file}")
                self.server_key = paramiko.RSAKey.from_private_key_file(self.key_file)
                print("SSH 服務器金鑰載入成功")
            else:
                # 生成新金鑰並儲存
                print(f"生成新的 SSH 金鑰: {self.key_file}")
                self.server_key = paramiko.RSAKey.generate(2048)
                self.server_key.write_private_key_file(self.key_file)
                print("SSH 服務器金鑰已生成並儲存")
                
        except Exception as e:
            print(f"處理 SSH 金鑰失敗: {e}")
            # 如果載入失敗，嘗試生成新的
            try:
                print("嘗試生成新金鑰...")
                self.server_key = paramiko.RSAKey.generate(2048)
                self.server_key.write_private_key_file(self.key_file)
                print("新 SSH 金鑰生成成功")
            except Exception as e2:
                print(f"生成 SSH 金鑰失敗: {e2}")
                sys.exit(1)
    
    def handle_client(self, client_socket, client_address):
        """處理客戶端連接"""
        print(f"SSH 連接來自: {client_address}")
        transport = None
        
        try:
            transport = paramiko.Transport(client_socket)
            transport.add_server_key(self.server_key)
            
            # 創建 SSH shell 處理器
            ssh_shell = SSHShell("unknown", client_address, self.fastapi_url)
            
            # 啟動服務器模式，直接傳遞 server 參數
            transport.start_server(server=ssh_shell)
            
            # 等待客戶端認證
            channel = transport.accept(timeout=60)
            if channel is None:
                print(f"SSH 認證失敗: {client_address}")
                return
            
            print(f"SSH 認證成功: {client_address}, 用戶: {ssh_shell.username}")
            
            # 設置 channel 到 shell 處理器
            ssh_shell.channel = channel
            
            # 運行 shell 會話
            ssh_shell.run_shell()
            
        except Exception as e:
            print(f"SSH 連接處理錯誤 {client_address}: {e}")
        finally:
            try:
                if transport:
                    transport.close()
                if client_socket:
                    client_socket.close()
            except Exception as e:
                print(f"關閉連接時發生錯誤: {e}")
        
        print(f"SSH 會話結束: {client_address}")
    
    def start(self):
        """啟動 SSH 服務器"""
        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((self.host, self.port))
            server_socket.listen(5)
            
            print(f"SSH 服務器啟動於 {self.host}:{self.port}")
            print(f"FastAPI 後端: {self.fastapi_url}")
            print("等待客戶端連接...")
            
            while True:
                try:
                    client_socket, client_address = server_socket.accept()
                    # 為每個客戶端創建新線程
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, client_address)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
                except KeyboardInterrupt:
                    print("\n正在關閉 SSH 服務器...")
                    break
                except Exception as e:
                    print(f"SSH 服務器錯誤: {e}")
                    
        except Exception as e:
            print(f"SSH 服務器啟動失敗: {e}")
        finally:
            try:
                server_socket.close()
            except:
                pass

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="SSH 檔案目錄服務器")
    parser.add_argument("--host", default="127.0.0.1", help="服務器地址")
    parser.add_argument("--port", type=int, default=2222, help="SSH 端口")
    parser.add_argument("--fastapi-url", default="http://localhost:8000", help="FastAPI 服務器 URL")
    
    args = parser.parse_args()
    
    server = SSHServer(args.host, args.port, args.fastapi_url)
    server.start()
