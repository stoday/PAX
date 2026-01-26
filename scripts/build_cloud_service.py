# -*- coding: utf-8 -*-
import os
import sys
import shutil
import urllib.request
import zipfile
import subprocess
import time
import traceback
import tomli

# English logs for stability with the agent console
def log(msg):
    try:
        print(f"[*] {msg}", flush=True)
    except:
        pass

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST_DIR = os.path.join(BASE_DIR, "dist", "cloud")
CLIENT_DIR = os.path.join(DIST_DIR, "client")
SERVER_DIR = os.path.join(DIST_DIR, "server")
LOG_FILE = os.path.join(BASE_DIR, "build_cloud_process.log")

# URLs
PYTHON_ZIP_URL = "https://www.python.org/ftp/python/3.10.11/python-3.10.11-embed-amd64.zip"
GET_PIP_URL = "https://bootstrap.pypa.io/get-pip.py"

def rmtree_with_retry(path, retries=5):
    if not os.path.exists(path):
        return
    log(f"Removing {path}...")
    for i in range(retries):
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
            return
        except Exception as e:
            if i == retries - 1:
                log(f"Failed to delete {path}: {str(e)}")
                raise e
            log(f"Retry deleting {path} ({i+1})...")
            time.sleep(2)

def download_file(url, dest):
    if os.path.exists(dest):
        log(f"File exists, skipping download: {os.path.basename(dest)}")
        return
    log(f"Downloading: {url}")
    urllib.request.urlretrieve(url, dest)

def setup_client_env():
    log("[1/4] Setting up Slim Embed Python for CLIENT only...")
    # 只有 Client 需要內建 Embed Python 以求「解壓即用」
    py_dir = os.path.join(CLIENT_DIR, "runtime", "python")
    os.makedirs(py_dir, exist_ok=True)
    
    zip_path = os.path.join(py_dir, "python_embed.zip")
    download_file(PYTHON_ZIP_URL, zip_path)
    
    log("Extracting Python for Client...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(py_dir)
    
    os.makedirs(os.path.join(py_dir, "Lib", "site-packages"), exist_ok=True)
    
    # 更新 ._pth 讓嵌入式環境抓得到 site-packages
    for f in os.listdir(py_dir):
        if f.endswith("._pth"):
            pth_file = os.path.join(py_dir, f)
            with open(pth_file, 'w', encoding='utf-8') as pf:
                pf.write("python310.zip\n.\nLib/site-packages\nimport site\n")
            break

    pip_script = os.path.join(py_dir, "get-pip.py")
    download_file(GET_PIP_URL, pip_script)
    log("Installing pip for Client...")
    subprocess.run([os.path.join(py_dir, "python.exe"), pip_script, "--no-warn-script-location"], check=True, stdout=subprocess.DEVNULL)
    
    # 為 Client 安裝僅需的基礎套件 (不要裝 akasha/torch 等大型庫)
    log("Installing slim requirements (requests, selenium, webdriver-manager, pydantic, beautifulsoup4, rich, pystray, pillow, tomli, browser_cookie3) for Client...")
    slim_reqs = ["requests", "selenium", "webdriver-manager", "python-dotenv", "rich", "pyfiglet", "pydantic", "beautifulsoup4", "pystray", "Pillow", "tomli", "browser_cookie3"]
    subprocess.run([os.path.join(py_dir, "python.exe"), "-m", "pip", "install"] + slim_reqs, check=True, stdout=subprocess.DEVNULL)
    
    if os.path.exists(pip_script): os.remove(pip_script)
    if os.path.exists(zip_path): os.remove(zip_path)

def build_client():
    log("[2/4] Packaging Client Source Code...")
    # 複製 Client 運作所需的腳本與介面
    folders = ["app", "core", "ui"]
    for folder in folders:
        src = os.path.join(BASE_DIR, folder)
        dst = os.path.join(CLIENT_DIR, folder)
        if os.path.exists(src):
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__"))
    
    # 複製雲端 Client 專屬 Runtime 邏輯
    runtime_dst = os.path.join(CLIENT_DIR, "runtime", "cloud", "client")
    os.makedirs(runtime_dst, exist_ok=True)
    shutil.copy2(os.path.join(BASE_DIR, "runtime", "__init__.py"), os.path.join(CLIENT_DIR, "runtime", "__init__.py"))
    shutil.copy2(os.path.join(BASE_DIR, "runtime", "cloud", "__init__.py"), os.path.join(CLIENT_DIR, "runtime", "cloud", "__init__.py"))
    shutil.copytree(os.path.join(BASE_DIR, "runtime", "cloud", "client"), runtime_dst, dirs_exist_ok=True)
    
    # 建立安全且脫敏的客戶端環境配置 (.env)
    log("Creating sanitized .env for Client...")
    src_env = os.path.join(BASE_DIR, ".env")
    if not os.path.exists(src_env):
        src_env = os.path.join(BASE_DIR, ".env.example")
    
    # 定義客戶端需要的 Key (移除 Gemini, Google Map 等敏感 Key)
    client_keys = [
        "ASP_NET_SESSION_ID", "CLIENT_TICKET", "CLIENT_USERNAME",
        "PAX_MODE", "PAX_SERVER_URL", "PAX_CLOUD_API_KEY",
        "AUTO_FILL_TIME"
    ]
    
    with open(src_env, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Create the client .env file
    with open(os.path.join(CLIENT_DIR, ".env"), 'w', encoding='utf-8') as f:
        f.write("# Pax Client Environment Settings (Sanitized)\n")
        f.write("PAX_MODE=cloud\n")
        
        # Load all from source env
        source_vars = {}
        if os.path.exists(src_env):
            with open(src_env, 'r', encoding='utf-8') as sf:
                for line in sf:
                    if "=" in line and not line.strip().startswith("#"):
                        parts = line.split("=", 1)
                        source_vars[parts[0].strip()] = parts[1].strip()

        # Try to read server_url from config.toml
        config_path = os.path.join(BASE_DIR, "config.toml")
        default_server_url = "http://localhost:8000"
        if os.path.exists(config_path):
            with open(config_path, "rb") as cf:
                config = tomli.load(cf)
                default_server_url = config.get("server", {}).get("server_url", default_server_url)

        # Write only allowed keys
        for key in client_keys:
            if key == "PAX_MODE": continue
            if key == "PAX_SERVER_URL":
                # 優先使用 config.toml 的值，如果 config.toml 沒設才看 source .env
                val = default_server_url if default_server_url != "http://localhost:8000" else source_vars.get(key, default_server_url)
                f.write(f"{key}={val}\n")
                continue
                
            if key in source_vars:
                f.write(f"{key}={source_vars[key]}\n")
            elif key == "AUTO_FILL_TIME":
                f.write("AUTO_FILL_TIME=17:55\n") # Default if missing
    
    # 建立啟動捷徑
    log("Creating PaxClient.bat...")
    bat_content = """@echo off
setlocal
set "ROOT=%~dp0"
set "PY_PATH=%ROOT%runtime\\python"
set "PATH=%PY_PATH%;%PY_PATH%\\Scripts;%PATH%"
set "PYTHONPATH=%ROOT%"
set "PAX_MODE=cloud"

if exist "%ROOT%.env" (
    for /f "usebackq tokens=1* delims==" %%A in (`findstr /b /c:"PAX_SERVER_URL=" "%ROOT%.env"`) do (
        set "PAX_SERVER_URL=%%B"
    )
)

if "%1"=="--debug" (
    echo [DEBUG MODE] Starting Pax in foreground...
    if defined PAX_SERVER_URL echo Using PAX_SERVER_URL=%PAX_SERVER_URL%
    "%PY_PATH%\\python.exe" "%ROOT%ui\\tray_app.py"
    pause
    exit /b
)

echo Starting Pax (Cloud Client Mode)...
if defined PAX_SERVER_URL echo Using PAX_SERVER_URL=%PAX_SERVER_URL%
start "" "%PY_PATH%\\pythonw.exe" "%ROOT%ui\\tray_app.py"
exit
"""
    with open(os.path.join(CLIENT_DIR, "PaxClient.bat"), "w", encoding="utf-8") as f:
        f.write(bat_content)
        
    # 複製版號設定
    shutil.copy2(os.path.join(BASE_DIR, "config.toml"), os.path.join(CLIENT_DIR, "config.toml"))

def build_server():
    log("[3/4] Preparing Server Source Package (No Python included)...")
    # 伺服器端只需程式碼與依賴清單，環境由您在伺服器手動配置
    os.makedirs(SERVER_DIR, exist_ok=True)
    
    # 複製伺服器「大腦」所需的所有核心功能與 MCP 工具
    folders = ["core", "tools", "app"]
    for folder in folders:
        src = os.path.join(BASE_DIR, folder)
        dst = os.path.join(SERVER_DIR, folder)
        if os.path.exists(src):
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "node_modules"))
    
    # 複製雲端 Server 專屬 Runtime 進入點 (FastAPI)
    server_code_dst = os.path.join(SERVER_DIR, "runtime", "cloud", "server")
    os.makedirs(server_code_dst, exist_ok=True)
    shutil.copy2(os.path.join(BASE_DIR, "runtime", "__init__.py"), os.path.join(SERVER_DIR, "runtime", "__init__.py"))
    shutil.copy2(os.path.join(BASE_DIR, "runtime", "cloud", "__init__.py"), os.path.join(SERVER_DIR, "runtime", "cloud", "__init__.py"))
    shutil.copytree(os.path.join(BASE_DIR, "runtime", "cloud", "server"), server_code_dst, dirs_exist_ok=True)
    
    # 複製完整的 requirements.txt 供伺服器 pip install
    shutil.copy2(os.path.join(BASE_DIR, "requirements.txt"), os.path.join(SERVER_DIR, "requirements.txt"))
    
    # 建立安全且脫敏的伺服器環境配置 (.env)
    log("Creating sanitized .env for Server...")
    src_env = os.path.join(BASE_DIR, ".env")
    if not os.path.exists(src_env):
        src_env = os.path.join(BASE_DIR, ".env.example")
    
    # 伺服器需要的 Key (保留 API Key，移除使用者的 Session)
    server_keys = [
        "GEMINI_API_KEY", "GOOGLE_MAP_API_KEY", "MCP_SERVER_PORT",
        "PAX_MODE", "PAX_CLOUD_API_KEY"
    ]
    
    with open(src_env, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    with open(os.path.join(SERVER_DIR, ".env"), 'w', encoding='utf-8') as f:
        f.write("# Pax Server Environment Settings (Clean Brain Mode)\n")
        # 直接指定 Cloud Server 必要的模式
        f.write("PAX_MODE=cloud\n")
        
        for line in lines:
            if "=" in line:
                key = line.split("=")[0].strip()
                if key == "PAX_MODE":
                    continue
                if key in server_keys:
                    f.write(line)
            elif line.strip().startswith("#") or not line.strip():
                f.write(line)
    
    # 建立啟動腳本範例 (假設您在伺服器端已建立好 venv)
    log("Creating server start scripts...")
    with open(os.path.join(SERVER_DIR, "start_server.sh"), "w", encoding="utf-8") as f:
        f.write("#!/bin/bash\n# 假設您已在伺服器端安裝好環境\nexport PYTHONPATH=$PYTHONPATH:.\npython3 runtime/cloud/server/main.py\n")
    
    with open(os.path.join(SERVER_DIR, "start_server.bat"), "w", encoding="utf-8") as f:
        f.write("@echo off\nset PYTHONPATH=.\npython runtime\\cloud\\server\\main.py\npause\n")

    # 複製版號設定
    shutil.copy2(os.path.join(BASE_DIR, "config.toml"), os.path.join(SERVER_DIR, "config.toml"))

def final_cleanup():
    log("[4/4] Final Cleanup...")
    # Remove pycache in dist
    for dist_root in [CLIENT_DIR, SERVER_DIR]:
        for root, dirs, files in os.walk(dist_root):
            if "__pycache__" in dirs:
                rmtree_with_retry(os.path.join(root, "__pycache__"))

if __name__ == "__main__":
    try:
        log("--- Cloud Service Build Started ---")
        if os.path.exists(DIST_DIR):
            rmtree_with_retry(DIST_DIR)
        os.makedirs(DIST_DIR)
        
        setup_client_env()
        build_client()
        build_server()
        final_cleanup()
        
        log("Done! Check cloud_dist folder.")
        log("- client/: Share this with users.")
        log("- server/: Deploy this to your Python server.")
    except Exception as e:
        log(f"Error: {str(e)}")
        traceback.print_exc()
        sys.exit(1)
