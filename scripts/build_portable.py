# -*- coding: utf-8 -*-
import os
import sys
import shutil
import urllib.request
import zipfile
import subprocess
import time
import traceback

# English logs for stability with the agent console
def log(msg):
    try:
        print(f"[*] {msg}", flush=True)
    except:
        pass

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST_DIR = os.path.join(BASE_DIR, "dist", "portable")
RUNTIME_DIR = os.path.join(DIST_DIR, "runtime")
PY_DIR = os.path.join(RUNTIME_DIR, "python")
NODE_DIR = os.path.join(RUNTIME_DIR, "node")
LOG_FILE = os.path.join(BASE_DIR, "build_process.log")

# URLs
PYTHON_ZIP_URL = "https://www.python.org/ftp/python/3.10.11/python-3.10.11-embed-amd64.zip"
GET_PIP_URL = "https://bootstrap.pypa.io/get-pip.py"
NODE_ZIP_URL = "https://nodejs.org/dist/v20.18.1/node-v20.18.1-win-x64.zip"

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

def setup_python():
    log("[1/6] Setting up Python Embedding Package...")
    if os.path.exists(os.path.join(PY_DIR, "python.exe")):
        log("Python already exists, skipping redo.")
        return
    
    os.makedirs(PY_DIR, exist_ok=True)
    zip_path = os.path.join(PY_DIR, "python_embed.zip")
    download_file(PYTHON_ZIP_URL, zip_path)
    
    log("Extracting Python...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(PY_DIR)
    
    os.makedirs(os.path.join(PY_DIR, "Lib", "site-packages"), exist_ok=True)

    # Find the ._pth file (e.g., python310._pth)
    pth_file = None
    for f in os.listdir(PY_DIR):
        if f.endswith("._pth"):
            pth_file = os.path.join(PY_DIR, f)
            log(f"Updating {f} to enable site-packages...")
            # Embedding python ignores Lib/site-packages unless we add it and 'import site'
            with open(pth_file, 'w', encoding='utf-8') as pf:
                pf.write("python310.zip\n.\nLib/site-packages\nimport site\n")
            break

    pip_script = os.path.join(PY_DIR, "get-pip.py")
    download_file(GET_PIP_URL, pip_script)
    log("Installing pip (this will be logged to build_process.log)...")
    with open(LOG_FILE, "a", encoding="utf-8") as log_f:
        subprocess.run([os.path.join(PY_DIR, "python.exe"), pip_script, "--no-warn-script-location"], 
                       stdout=log_f, stderr=log_f, check=True)
    
    if os.path.exists(pip_script): os.remove(pip_script)
    if os.path.exists(zip_path): os.remove(zip_path)

def setup_node():
    log("[2/6] Setting up Node.js Portable...")
    if os.path.exists(os.path.join(NODE_DIR, "node.exe")):
        log("Node.js already exists, skipping redo.")
        return
    
    os.makedirs(RUNTIME_DIR, exist_ok=True)
    node_zip = os.path.join(RUNTIME_DIR, "node.zip")
    download_file(NODE_ZIP_URL, node_zip)

    temp_extract = os.path.join(RUNTIME_DIR, "temp_node")
    rmtree_with_retry(temp_extract)
    os.makedirs(temp_extract, exist_ok=True)

    log("Extracting Node.js...")
    with zipfile.ZipFile(node_zip, 'r') as zip_ref:
        zip_ref.extractall(temp_extract)
    
    subdirs = [d for d in os.listdir(temp_extract) if os.path.isdir(os.path.join(temp_extract, d))]
    if subdirs:
        node_src = os.path.join(temp_extract, subdirs[0])
        log("Moving Node files...")
        os.makedirs(NODE_DIR, exist_ok=True)
        for f in os.listdir(node_src):
            src_f = os.path.join(node_src, f)
            dst_f = os.path.join(NODE_DIR, f)
            if os.path.isdir(src_f):
                shutil.copytree(src_f, dst_f)
            else:
                shutil.copy2(src_f, dst_f)
    
    rmtree_with_retry(temp_extract)
    if os.path.exists(node_zip): os.remove(node_zip)

def install_requirements():
    log("[3/6] Installing requirements...")
    req_file = os.path.join(BASE_DIR, "requirements.txt")
    if not os.path.exists(req_file): return

    python_exe = os.path.join(PY_DIR, "python.exe")
    
    # Simple check to skip if already done (akasha is usually the last one)
    if os.path.exists(os.path.join(PY_DIR, "Lib", "site-packages", "akasha")):
        log("Requirements seem to be already installed. Skipping.")
        return

    log("Executing pip install... This might fail due to file locks (Dropbox/AV), we will retry 3 times.")
    for i in range(3):
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as log_f:
                # Added --no-cache-dir and --retries 10 for more stability
                subprocess.run([python_exe, "-m", "pip", "install", "--no-cache-dir", "-r", req_file, "--no-warn-script-location"], 
                               stdout=log_f, stderr=log_f, check=True)
            log("Pip install successful!")
            return
        except Exception as e:
            log(f"Pip install failed (attempt {i+1}/3): {str(e)}")
            if i < 2:
                log("Waiting 5 seconds before retrying...")
                time.sleep(5)
            else:
                raise e

def cleanup_size():
    log("[3.5/6] Cleaning up large unused packages (torch, etc.) for size optimization...")
    site_packages = os.path.join(PY_DIR, "Lib", "site-packages")
    if not os.path.exists(site_packages): return
    
    # Prefix of packages that are safe to remove in light mode
    # Keep onnxruntime because chromadb (used by akasha) requires it for default embeddings
    to_remove_prefixes = [
        "torch", "transformers", "sentence_transformers", 
        "scipy", "pyarrow", "matplotlib"
    ]
    
    removed_count = 0
    for folder in os.listdir(site_packages):
        folder_path = os.path.join(site_packages, folder)
        low_folder = folder.lower()
        
        if any(low_folder.startswith(p) for p in to_remove_prefixes):
            try:
                rmtree_with_retry(folder_path)
                log(f"Removed large package/info: {folder}")
                removed_count += 1
            except Exception as e:
                log(f"Failed to remove {folder}: {e}")
                
    log(f"Size optimization completed. Removed {removed_count} folders/packages.")


def copy_sources():
    log("[4/6] Copying project sources...")
    
    # Copy specific files to DIST_DIR
    files_to_copy = ["config.toml"]
    for f_name in files_to_copy:
        src_file = os.path.join(BASE_DIR, f_name)
        dst_file = os.path.join(DIST_DIR, f_name)
        if os.path.exists(src_file):
            shutil.copy2(src_file, dst_file)
            log(f"Copied file: {f_name}")

    folders = ["app", "core", "tools", "ui", "bin"] # Removed runtime from main loop
    for folder in folders:
        src = os.path.join(BASE_DIR, folder)
        if os.path.exists(src) and os.path.isdir(src):
            dst = os.path.join(DIST_DIR, folder)
            rmtree_with_retry(dst)
            shutil.copytree(src, dst)
    
    # Handle runtime specifically to avoid deleting built runtimes (python/node)
    src_runtime = os.path.join(BASE_DIR, "runtime")
    if os.path.exists(src_runtime):
        for sub in os.listdir(src_runtime):
            # Skip the binary runtime directories we just created
            if sub in ["python", "node", "temp_node"]:
                continue
                
            src_sub = os.path.join(src_runtime, sub)
            dst_sub = os.path.join(RUNTIME_DIR, sub)
            
            if os.path.isdir(src_sub):
                if os.path.exists(dst_sub): rmtree_with_retry(dst_sub)
                shutil.copytree(src_sub, dst_sub)
                log(f"Copied runtime source dir: {sub}")
            else:
                shutil.copy2(src_sub, dst_sub)
                log(f"Copied runtime source file: {sub}")
    
    # 處理 .env 檔案
    src_env = os.path.join(BASE_DIR, ".env")
    dst_env = os.path.join(DIST_DIR, ".env")
    
    lines = []
    if os.path.exists(src_env):
        with open(src_env, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    
    with open(dst_env, 'w', encoding='utf-8') as f:
        f.write("# Pax Portable Environment Settings\n")
        has_mode = False
        for line in lines:
            if line.strip().startswith("PAX_MODE="):
                f.write("PAX_MODE=local\n")
                has_mode = True
            else:
                f.write(line)
        if not has_mode:
            f.write("PAX_MODE=local\n")

def create_launcher():
    log("[5/6] Creating Pax.bat launcher...")
    bat_content = """@echo off
setlocal
set "ROOT=%~dp0"
set "PY_PATH=%ROOT%runtime\\python"
set "NODE_PATH=%ROOT%runtime\\node"
set "PATH=%PY_PATH%;%PY_PATH%\\Scripts;%NODE_PATH%;%PATH%"
set "PYTHONPATH=%ROOT%"
set "PAX_MODE=local"

if "%1"=="--debug" (
    echo [DEBUG MODE] Starting Pax in foreground...
    "%PY_PATH%\\python.exe" "%ROOT%ui\\tray_app.py"
    pause
    exit /b
)

echo Starting Pax (Portable Mode)...
start "" "%PY_PATH%\\pythonw.exe" "%ROOT%ui\\tray_app.py"
exit
"""
    with open(os.path.join(DIST_DIR, "Pax.bat"), "w", encoding="utf-8") as f:
        f.write(bat_content)

def clean_up():
    log("[6/6] Final cleanup...")
    for root, dirs, files in os.walk(DIST_DIR):
        if "__pycache__" in dirs:
            rmtree_with_retry(os.path.join(root, "__pycache__"))

if __name__ == "__main__":
    try:
        # Initialize Log
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write("--- Build Start ---\n")
            
        if not os.path.exists(DIST_DIR):
            os.makedirs(DIST_DIR)
            
        setup_python()
        setup_node()
        install_requirements()
        cleanup_size()
        copy_sources()
        create_launcher()
        clean_up()
        log("Done! Check portable_dist folder.")
    except Exception as e:
        log(f"Error: {str(e)}")
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            traceback.print_exc(file=f)
        sys.exit(1)
