# SSH 檔案目錄服務使用說明

## 🔒 SSH 服務功能

SSH（Secure Shell）版本提供了比 Telnet 更安全的遠端連接方式，支援：
- **加密通信** - 所有數據都經過加密傳輸
- **身份驗證** - 支援用戶名/密碼認證
- **安全連接** - 防止中間人攻擊
- **跨平台支援** - 可從 Linux/macOS/Windows 連接

## 🚀 快速開始

### 1. 安裝依賴套件
```bash
# 安裝所有依賴（包括 SSH 支援）
pip install -r requirements.txt

# 或手動安裝 SSH 相關套件
pip install paramiko
```

### 2. 啟動 SSH 服務器
```bash
# 啟動所有服務（包括 SSH）
python start_services.py

# 僅啟動 SSH 服務器
python start_services.py --mode ssh

# 自訂 SSH 埠號
python start_services.py --ssh-port 2222
```

### 3. 從遠端 Linux 系統連接

#### 使用標準 SSH 客戶端
```bash
# 基本連接
ssh admin@your-server-ip -p 2222

# 指定用戶連接
ssh user@your-server-ip -p 2222

# 如果是在同一台機器測試
ssh admin@localhost -p 2222
```

#### 使用內建的 Python SSH 客戶端
```bash
# 互動模式
python examples/ssh_client_example.py --host your-server-ip --port 2222

# 自動演示
python examples/ssh_client_example.py --host your-server-ip --demo

# 執行單一命令
python examples/ssh_client_example.py --host your-server-ip -c "ls /"
```

## 👥 預設用戶帳號

| 用戶名 | 密碼 | 說明 |
|--------|------|------|
| `admin` | `password123` | 管理員帳號 |
| `user` | `userpass` | 一般用戶 |
| `guest` | `guest` | 訪客帳號 |

⚠️ **安全提醒**: 這些是範例帳號，實際使用時請務必更改密碼！

## 🌐 從不同作業系統連接

### Linux 連接範例
```bash
# Ubuntu/Debian/CentOS
ssh admin@192.168.1.100 -p 2222

# 如果出現主機金鑰警告，可以使用：
ssh -o StrictHostKeyChecking=no admin@192.168.1.100 -p 2222
```

### macOS 連接範例
```bash
# macOS 內建 SSH 客戶端
ssh admin@192.168.1.100 -p 2222

# 使用終端機
Terminal > ssh admin@192.168.1.100 -p 2222
```

### Windows 連接範例
```powershell
# Windows 10/11 內建 SSH 客戶端
ssh admin@192.168.1.100 -p 2222

# 使用 PuTTY
# Host: 192.168.1.100, Port: 2222, Protocol: SSH
```

## 📋 可用的 SSH 命令

SSH 服務器支援類似 Linux 命令列的介面：

```bash
# 檔案和目錄操作
ls              # 列出當前目錄
ls /path        # 列出指定路徑
cd /path        # 切換目錄
pwd             # 顯示當前路徑
info file.txt   # 顯示檔案詳細資訊

# 系統資訊
whoami          # 顯示當前用戶
uname           # 顯示系統資訊
status          # 顯示服務器狀態
drives          # 顯示磁碟機（Windows）

# 介面控制
help            # 顯示幫助
clear           # 清屏
quit/exit       # 退出連接
```

## 🔧 進階配置

### 1. 自訂用戶帳號
編輯 `clockmate/ssh_server.py` 中的用戶清單：

```python
self.users = {
    "your_username": "your_secure_password",
    "another_user": "another_password"
}
```

### 2. 修改 SSH 埠號
```bash
# 啟動時指定埠號
python start_services.py --ssh-port 22222

# 或修改程式中的預設值
```

### 3. 限制連接 IP
修改 `ssh_server.py` 中的 `host` 參數：

```python
# 僅本機連接
start_ssh_server(host="127.0.0.1", port=2222)

# 允許所有 IP 連接
start_ssh_server(host="0.0.0.0", port=2222)

# 指定網段
start_ssh_server(host="192.168.1.100", port=2222)
```

## 🔐 SSH 金鑰管理

### 自動生成的主機金鑰
程式會自動生成 RSA 主機金鑰：
- 檔案位置: `ssh_host_rsa_key`
- 金鑰長度: 2048 位元
- 首次連接時會提示接受主機金鑰

### 客戶端金鑰指紋
首次連接時會看到類似訊息：
```
The authenticity of host '[localhost]:2222' can't be established.
RSA key fingerprint is SHA256:xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.
Are you sure you want to continue connecting (yes/no)?
```

輸入 `yes` 接受金鑰。

## 🐧 Linux 系統連接範例

### 從 Ubuntu 連接
```bash
# 安裝 SSH 客戶端（通常已預安裝）
sudo apt update
sudo apt install openssh-client

# 連接到 Windows SSH 服務器
ssh admin@192.168.1.100 -p 2222
```

### 從 CentOS/RHEL 連接
```bash
# 安裝 SSH 客戶端
sudo yum install openssh-clients

# 連接
ssh admin@192.168.1.100 -p 2222
```

### 使用 SSH 設定檔
在 Linux 上建立 `~/.ssh/config`:

```
Host fileserver
    HostName 192.168.1.100
    Port 2222
    User admin
    StrictHostKeyChecking no
```

然後可以簡單地執行：
```bash
ssh fileserver
```

## 🚨 安全注意事項

### ⚠️ 重要警告
這是一個**範例程式**，不建議直接在生產環境使用，因為：

1. **弱密碼** - 使用預設的簡單密碼
2. **無加密儲存** - 密碼以明文儲存
3. **無存取控制** - 可以存取整個檔案系統
4. **無日誌記錄** - 沒有詳細的存取日誌
5. **無防護機制** - 沒有暴力破解防護

### 🛡️ 生產環境建議

如果要用於實際環境，建議：

1. **強化密碼策略**
   ```python
   # 使用強密碼
   "admin": "Complex_Password_2024!"
   ```

2. **使用公鑰認證**
   ```python
   def check_auth_publickey(self, username, key):
       # 實作公鑰驗證
       authorized_keys = load_authorized_keys(username)
       return key in authorized_keys
   ```

3. **限制檔案存取**
   ```python
   # 限制可存取的目錄
   allowed_paths = ["/home/user", "/var/log"]
   ```

4. **加入日誌記錄**
   ```python
   import logging
   logging.info(f"User {username} accessed {path}")
   ```

5. **設定防火牆**
   ```bash
   # 僅允許特定 IP 存取 SSH 埠
   ufw allow from 192.168.1.0/24 to any port 2222
   ```

## 🔍 故障排除

### SSH 連接問題

1. **連接被拒絕**
   ```
   Connection refused
   ```
   - 檢查服務器是否在運行
   - 確認埠號是否正確
   - 檢查防火牆設定

2. **認證失敗**
   ```
   Permission denied (publickey,password)
   ```
   - 檢查用戶名和密碼
   - 確認用戶帳號是否存在

3. **主機金鑰錯誤**
   ```
   Host key verification failed
   ```
   - 刪除客戶端的 known_hosts 記錄
   ```bash
   ssh-keygen -R [localhost]:2222
   ```

4. **埠號被佔用**
   ```
   Address already in use
   ```
   ```bash
   # Windows
   netstat -ano | findstr :2222
   taskkill /PID <PID> /F
   
   # Linux
   netstat -tlnp | grep :2222
   kill -9 <PID>
   ```

### 效能問題

1. **連接速度慢**
   - 減少同時連線數
   - 增加接收緩衝區大小

2. **記憶體使用過高**
   - 限制同時連線數
   - 實作連線池管理

## 📝 使用範例腳本

### 自動化連接腳本
```bash
#!/bin/bash
# connect-to-fileserver.sh

HOST="192.168.1.100"
PORT="2222"
USER="admin"

echo "連接到檔案服務器..."
echo "主機: $HOST:$PORT"
echo "用戶: $USER"

ssh -o StrictHostKeyChecking=no $USER@$HOST -p $PORT
```

### 批量檔案查詢
```python
# bulk_query.py
import paramiko

def query_files(host, port, username, password, paths):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(host, port, username, password)
        
        for path in paths:
            stdin, stdout, stderr = client.exec_command(f"info {path}")
            result = stdout.read().decode()
            print(f"=== {path} ===")
            print(result)
            
    finally:
        client.close()

# 使用範例
query_files("192.168.1.100", 2222, "admin", "password123", 
           ["setup.py", "README.md", "/etc/hosts"])
```

---

## 🎯 總結

SSH 版本的檔案目錄服務提供了：
- ✅ 安全的加密連接
- ✅ 跨平台相容性
- ✅ 標準 SSH 協議支援
- ✅ Linux 風格的命令介面
- ✅ 多用戶支援

從任何支援 SSH 的 Linux 系統都可以輕鬆連接並瀏覽遠端 Windows 電腦的檔案系統！