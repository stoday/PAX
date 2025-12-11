"""
檔案目錄服務啟動器 - 同時啟動 FastAPI、Telnet 和 SSH 服務器
"""
import sys
import time
import subprocess

def start_ssh_server():
    """啟動 SSH 服務器"""
    print("等待服務器啟動...")
    time.sleep(3)  # 等待服務器完全啟動
    
    print("正在啟動 SSH 服務器 (純文字版)...")
    
    try:
        from clockmate.ssh_server_plain import SSHServer
        ssh_server = SSHServer(host="0.0.0.0", port=2222, fastapi_url="http://127.0.0.1:8000")
        ssh_server.start()
    except ImportError as e:
        print(f"導入 SSH 服務器失敗: {e}")
    except Exception as e:
        print(f"啟動 SSH 服務器時發生錯誤: {e}")

def check_dependencies():
    """檢查必要的依賴套件"""
    required_packages = ["fastapi", "uvicorn", "requests"]
    optional_packages = {"paramiko": "SSH 功能"}
    missing_packages = []
    missing_optional = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    for package, feature in optional_packages.items():
        try:
            __import__(package)
        except ImportError:
            missing_optional.append(f"{package} ({feature})")
    
    if missing_packages:
        print(f"缺少必要套件: {', '.join(missing_packages)}")
        print("請執行以下命令安裝依賴:")
        print("pip install -r requirements.txt")
        return False
    
    if missing_optional:
        print(f"缺少選用套件: {', '.join(missing_optional)}")
        print("這些功能將無法使用")
    
    return True

def main():
    """主函數"""
    start_ssh_server()

def install_dependencies():
    """安裝依賴套件"""
    print("正在安裝依賴套件...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("依賴套件安裝完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"安裝依賴套件失敗: {e}")
        return False

if __name__ == "__main__":
    start_ssh_server()