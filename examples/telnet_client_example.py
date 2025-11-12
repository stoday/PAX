"""
Telnet 客戶端範例 - 連接到 Telnet 服務器並與檔案目錄服務互動
"""
import socket
import threading
import time
import sys
from typing import Optional

class TelnetClient:
    """Telnet 客戶端類"""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 2323):
        self.host = host
        self.port = port
        self.socket: Optional[socket.socket] = None
        self.connected = False
        self.receiving = False
    
    def connect(self) -> bool:
        """連接到 Telnet 服務器"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.connected = True
            print(f"已連接到 {self.host}:{self.port}")
            
            # 啟動接收線程
            self.receiving = True
            receive_thread = threading.Thread(target=self.receive_messages)
            receive_thread.daemon = True
            receive_thread.start()
            
            # 等待服務器的登入提示
            time.sleep(1)
            
            return True
            
        except Exception as e:
            print(f"連接失敗: {e}")
            return False
    
    def authenticate(self, username: str, password: str) -> bool:
        """進行認證"""
        if not self.connected or not self.socket:
            print("未連接到服務器")
            return False
        
        try:
            # 發送用戶名
            self.socket.send((username + "\n").encode('utf-8'))
            time.sleep(0.5)
            
            # 發送密碼
            self.socket.send((password + "\n").encode('utf-8'))
            time.sleep(1)
            
            # 這裡可以添加檢查認證結果的邏輯
            # 簡單起見，我們假設如果沒有斷開連接就是成功
            return self.connected
            
        except Exception as e:
            print(f"認證失敗: {e}")
            self.disconnect()
            return False
    
    def disconnect(self):
        """斷開連接"""
        self.connected = False
        self.receiving = False
        
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            
        print("已斷開連接")
    
    def send_command(self, command: str):
        """發送命令到服務器"""
        if not self.connected or not self.socket:
            print("未連接到服務器")
            return False
        
        try:
            self.socket.send((command + "\n").encode('utf-8'))
            return True
        except Exception as e:
            print(f"發送命令失敗: {e}")
            self.disconnect()
            return False
    
    def receive_messages(self):
        """接收服務器訊息的線程"""
        buffer = ""
        
        while self.receiving and self.socket:
            try:
                data = self.socket.recv(4096).decode('utf-8')
                if not data:
                    break
                
                buffer += data
                
                # 處理完整的回應
                while '\n' in buffer or '> ' in buffer:
                    if '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        if line.strip():
                            print(line)
                    elif '> ' in buffer and not '\n' in buffer:
                        # 處理提示符
                        parts = buffer.split('> ', 1)
                        if len(parts) > 1:
                            print(parts[0] + '> ', end='', flush=True)
                            buffer = parts[1]
                        else:
                            print(buffer, end='', flush=True)
                            buffer = ""
                        break
                    
            except socket.timeout:
                continue
            except Exception as e:
                if self.receiving:
                    print(f"接收訊息時發生錯誤: {e}")
                break
        
        if self.receiving:
            print("\n連接已中斷")
            self.connected = False
    
    def interactive_mode(self):
        """互動模式"""
        print("\n=== Telnet 檔案目錄客戶端 ===")
        print("輸入命令與服務器互動")
        print("輸入 'quit' 或 'exit' 退出")
        print("輸入 'help' 查看可用命令\n")
        
        while self.connected:
            try:
                command = input()
                
                if command.strip().lower() in ['quit', 'exit', 'disconnect']:
                    self.send_command("quit")
                    time.sleep(0.5)  # 等待服務器回應
                    break
                
                if command.strip():
                    if not self.send_command(command.strip()):
                        break
                    
            except KeyboardInterrupt:
                print("\n正在斷開連接...")
                break
            except EOFError:
                break
        
        self.disconnect()

def demo_commands(client: TelnetClient):
    """演示基本命令"""
    if not client.connected:
        return
    
    print("\n=== 自動演示模式 ===")
    
    commands = [
        ("status", "檢查服務器狀態"),
        ("help", "顯示幫助信息"),
        ("pwd", "顯示當前路徑"),
        ("drives", "顯示可用磁碟機"),
        ("ls", "列出當前目錄"),
        ("ls C:\\", "列出 C:\\ 目錄"),
        ("info setup.py", "顯示 setup.py 檔案資訊")
    ]
    
    for command, description in commands:
        print(f"\n> 執行: {command} ({description})")
        client.send_command(command)
        time.sleep(2)  # 等待回應
    
    print("\n演示完成！")

def main():
    """主函數"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Telnet 檔案目錄客戶端")
    parser.add_argument("--host", default="127.0.0.1", help="服務器主機 (預設: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=2323, help="服務器埠號 (預設: 2323)")
    parser.add_argument("--username", "-u", default="admin", help="登入用戶名 (預設: admin)")
    parser.add_argument("--password", "-p", help="登入密碼 (預設: password123)")
    parser.add_argument("--demo", action="store_true", help="執行自動演示")
    
    args = parser.parse_args()
    
    # 預設密碼
    password = args.password or "password123"
    
    # 創建客戶端
    client = TelnetClient(args.host, args.port)
    
    # 連接到服務器
    if not client.connect():
        print("無法連接到服務器，請確認:")
        print("1. Telnet 服務器是否在運行")
        print("2. 主機和埠號是否正確")
        print("3. 防火牆設定是否允許連接")
        return 1
    
    # 進行認證
    print(f"正在以 {args.username} 身份登入...")
    if not client.authenticate(args.username, password):
        print("認證失敗，請檢查用戶名和密碼")
        print("可用帳號: admin/password123, user/userpass, guest/guest, demo/demo123")
        return 1
    
    print("認證成功！")
    
    try:
        if args.demo:
            # 演示模式
            time.sleep(1)  # 等待歡迎訊息
            demo_commands(client)
            time.sleep(2)
            client.send_command("quit")
            time.sleep(1)
        else:
            # 互動模式
            time.sleep(1)  # 等待歡迎訊息
            client.interactive_mode()
            
    except Exception as e:
        print(f"客戶端錯誤: {e}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())