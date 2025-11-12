"""
SSH 客戶端範例 - 連接到 SSH 檔案目錄服務器
"""
import sys
import threading
import time
from typing import Optional

try:
    import paramiko
except ImportError:
    print("需要安裝 paramiko 套件: pip install paramiko")
    sys.exit(1)

class SSHFileClient:
    """SSH 檔案服務器客戶端"""
    
    def __init__(self, hostname: str = "127.0.0.1", port: int = 2222, username: str = "admin", password: str = "password123"):
        self.hostname = hostname
        self.port = port
        self.username = username
        self.password = password
        self.ssh_client: Optional[paramiko.SSHClient] = None
        self.channel: Optional[paramiko.Channel] = None
        self.connected = False
        self.receiving = False
    
    def connect(self) -> bool:
        """連接到 SSH 服務器"""
        try:
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            print(f"正在連接到 {self.hostname}:{self.port}...")
            
            self.ssh_client.connect(
                hostname=self.hostname,
                port=self.port,
                username=self.username,
                password=self.password,
                timeout=10
            )
            
            print("SSH 認證成功")
            
            # 開啟一個互動式 shell 通道
            self.channel = self.ssh_client.invoke_shell(term='xterm', width=80, height=24)
            
            if self.channel:
                self.connected = True
                print("已建立 SSH 通道")
                
                # 啟動接收線程
                self.receiving = True
                receive_thread = threading.Thread(target=self.receive_messages)
                receive_thread.daemon = True
                receive_thread.start()
                
                return True
            else:
                print("無法建立 SSH 通道")
                return False
                
        except paramiko.AuthenticationException:
            print("SSH 認證失敗 - 請檢查用戶名和密碼")
            return False
        except paramiko.SSHException as e:
            print(f"SSH 連接錯誤: {e}")
            return False
        except Exception as e:
            print(f"連接失敗: {e}")
            return False
    
    def disconnect(self):
        """斷開 SSH 連接"""
        self.connected = False
        self.receiving = False
        
        if self.channel:
            try:
                self.channel.close()
            except:
                pass
        
        if self.ssh_client:
            try:
                self.ssh_client.close()
            except:
                pass
        
        print("SSH 連接已關閉")
    
    def send_command(self, command: str):
        """發送命令到 SSH 服務器"""
        if not self.connected or not self.channel:
            print("未連接到 SSH 服務器")
            return False
        
        try:
            self.channel.send(command + '\n')
            return True
        except Exception as e:
            print(f"發送命令失敗: {e}")
            self.disconnect()
            return False
    
    def receive_messages(self):
        """接收 SSH 服務器訊息的線程"""
        buffer = b""
        
        while self.receiving and self.channel:
            try:
                # 檢查是否有數據可讀
                if self.channel.recv_ready():
                    data = self.channel.recv(4096)
                    if not data:
                        break
                    
                    buffer += data
                    
                    # 處理完整的行
                    while b'\n' in buffer:
                        line, buffer = buffer.split(b'\n', 1)
                        try:
                            decoded_line = line.decode('utf-8', errors='replace')
                            # 移除 ANSI 轉義序列（簡單版本）
                            import re
                            clean_line = re.sub(r'\x1b\[[0-9;]*m', '', decoded_line)
                            print(clean_line)
                        except:
                            pass
                    
                    # 處理剩餘的不完整數據
                    if buffer:
                        try:
                            decoded_buffer = buffer.decode('utf-8', errors='replace')
                            if not decoded_buffer.endswith(('$ ', '# ', '> ')):
                                print(decoded_buffer, end='', flush=True)
                                buffer = b""
                        except:
                            pass
                
                else:
                    time.sleep(0.1)
                    
            except Exception as e:
                if self.receiving:
                    print(f"接收訊息時發生錯誤: {e}")
                break
        
        if self.receiving:
            print("\nSSH 連接已中斷")
            self.connected = False
    
    def interactive_mode(self):
        """互動模式"""
        print("\n=== SSH 檔案目錄客戶端 ===")
        print("輸入命令與 SSH 服務器互動")
        print("輸入 'quit' 或 'exit' 退出")
        print("按 Ctrl+C 也可以退出\n")
        
        # 等待歡迎訊息
        time.sleep(1)
        
        while self.connected:
            try:
                command = input()
                
                if command.strip().lower() in ['quit', 'exit', 'logout']:
                    self.send_command("quit")
                    time.sleep(0.5)
                    break
                
                if command.strip():
                    if not self.send_command(command.strip()):
                        break
                    
            except KeyboardInterrupt:
                print("\n正在斷開 SSH 連接...")
                break
            except EOFError:
                break
        
        self.disconnect()
    
    def execute_single_command(self, command: str) -> str:
        """執行單一命令並返回結果"""
        if not self.ssh_client:
            return "未連接到 SSH 服務器"
        
        try:
            stdin, stdout, stderr = self.ssh_client.exec_command(command, timeout=10)
            
            # 讀取輸出
            output = stdout.read().decode('utf-8', errors='replace')
            error = stderr.read().decode('utf-8', errors='replace')
            
            result = ""
            if output:
                result += output
            if error:
                result += f"\nError: {error}"
            
            return result
            
        except Exception as e:
            return f"執行命令失敗: {e}"

def demo_commands(client: SSHFileClient):
    """演示基本命令"""
    if not client.connected:
        return
    
    print("\n=== SSH 自動演示模式 ===")
    
    commands = [
        ("help", "顯示幫助信息"),
        ("pwd", "顯示當前路徑"),
        ("whoami", "顯示當前用戶"),
        ("uname", "顯示系統信息"),
        ("status", "檢查服務器狀態"),
        ("ls", "列出當前目錄"),
        ("ls C:\\", "列出 C:\\ 目錄 (Windows)"),
        ("info setup.py", "顯示 setup.py 檔案資訊"),
        ("clear", "清屏")
    ]
    
    for command, description in commands:
        print(f"\n> 執行: {command} ({description})")
        client.send_command(command)
        time.sleep(3)  # 等待回應
    
    print("\nSSH 演示完成！")

def main():
    """主函數"""
    import argparse
    
    parser = argparse.ArgumentParser(description="SSH 檔案目錄客戶端")
    parser.add_argument("--host", default="127.0.0.1", help="SSH 服務器主機 (預設: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=2222, help="SSH 服務器埠號 (預設: 2222)")
    parser.add_argument("--username", "-u", default="admin", help="SSH 用戶名 (預設: admin)")
    parser.add_argument("--password", "-p", help="SSH 密碼 (預設: password123)")
    parser.add_argument("--demo", action="store_true", help="執行自動演示")
    parser.add_argument("--command", "-c", help="執行單一命令後退出")
    
    args = parser.parse_args()
    
    # 預設密碼
    password = args.password or "password123"
    
    # 創建 SSH 客戶端
    client = SSHFileClient(args.host, args.port, args.username, password)
    
    # 連接到服務器
    if not client.connect():
        print("\n無法連接到 SSH 服務器，請確認:")
        print("1. SSH 服務器是否在運行")
        print("2. 主機和埠號是否正確")
        print("3. 用戶名和密碼是否正確")
        print("4. 防火牆設定是否允許連接")
        print(f"\n預設連接資訊:")
        print(f"服務器: {args.host}:{args.port}")
        print(f"用戶: {args.username}")
        print(f"密碼: {password}")
        return 1
    
    try:
        if args.command:
            # 單一命令模式
            time.sleep(1)  # 等待初始化
            result = client.execute_single_command(args.command)
            print(result)
        elif args.demo:
            # 演示模式
            time.sleep(2)  # 等待歡迎訊息
            demo_commands(client)
            time.sleep(2)
            client.send_command("quit")
            time.sleep(1)
        else:
            # 互動模式
            time.sleep(1)  # 等待歡迎訊息
            client.interactive_mode()
            
    except Exception as e:
        print(f"SSH 客戶端錯誤: {e}")
    finally:
        client.disconnect()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())