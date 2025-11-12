"""
FastAPI 服務器 - 提供檔案目錄瀏覽功能
"""
import os
import json
from typing import List, Dict, Any
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
import uvicorn
from datetime import datetime

app = FastAPI(
    title="檔案目錄服務",
    description="透過 API 提供檔案目錄瀏覽功能",
    version="1.0.0"
)

@app.get("/")
async def root():
    """根路徑 - 服務狀態檢查"""
    return {
        "message": "檔案目錄服務正在運行",
        "status": "active",
        "timestamp": datetime.now().isoformat(),
        "endpoints": [
            "/list-directory",
            "/get-file-info",
            "/get-drives"
        ]
    }

@app.get("/list-directory")
async def list_directory(path: str = Query(".", description="要列出的目錄路徑")):
    """
    列出指定目錄的內容
    
    Args:
        path: 目錄路徑，預設為當前目錄
        
    Returns:
        包含檔案和目錄列表的 JSON 回應
    """
    try:
        # 確保路徑安全，防止路徑遍歷攻擊
        target_path = Path(path).resolve()
        
        if not target_path.exists():
            raise HTTPException(status_code=404, detail=f"路徑不存在: {path}")
        
        if not target_path.is_dir():
            raise HTTPException(status_code=400, detail=f"路徑不是目錄: {path}")
        
        items = []
        
        for item in target_path.iterdir():
            try:
                item_info = {
                    "name": item.name,
                    "path": str(item),
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else None,
                    "modified": datetime.fromtimestamp(item.stat().st_mtime).isoformat(),
                    "created": datetime.fromtimestamp(item.stat().st_ctime).isoformat()
                }
                
                if item.is_file():
                    item_info["extension"] = item.suffix
                
                items.append(item_info)
            except (OSError, PermissionError):
                # 跳過無法讀取的項目
                continue
        
        # 按名稱排序，目錄在前
        items.sort(key=lambda x: (x["type"] == "file", x["name"].lower()))
        
        return {
            "success": True,
            "path": str(target_path),
            "parent": str(target_path.parent) if target_path.parent != target_path else None,
            "items": items,
            "total_items": len(items),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"讀取目錄時發生錯誤: {str(e)}")

@app.get("/get-file-info")
async def get_file_info(path: str = Query(..., description="檔案路徑")):
    """
    獲取指定檔案的詳細資訊
    
    Args:
        path: 檔案路徑
        
    Returns:
        檔案詳細資訊
    """
    try:
        target_path = Path(path).resolve()
        
        if not target_path.exists():
            raise HTTPException(status_code=404, detail=f"檔案不存在: {path}")
        
        stat = target_path.stat()
        
        return {
            "success": True,
            "name": target_path.name,
            "path": str(target_path),
            "type": "directory" if target_path.is_dir() else "file",
            "size": stat.st_size,
            "size_human": _format_size(stat.st_size),
            "extension": target_path.suffix if target_path.is_file() else None,
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "accessed": datetime.fromtimestamp(stat.st_atime).isoformat(),
            "parent": str(target_path.parent),
            "is_hidden": target_path.name.startswith('.'),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取檔案資訊時發生錯誤: {str(e)}")

@app.get("/get-drives")
async def get_drives():
    """
    獲取系統磁碟機列表（僅限 Windows）
    
    Returns:
        可用磁碟機列表
    """
    try:
        import platform
        
        if platform.system() != "Windows":
            return {
                "success": True,
                "message": "非 Windows 系統，返回根目錄",
                "drives": ["/"],
                "timestamp": datetime.now().isoformat()
            }
        
        import string
        drives = []
        
        for letter in string.ascii_uppercase:
            drive = f"{letter}:\\"
            if os.path.exists(drive):
                try:
                    # 嘗試獲取磁碟機資訊
                    stat = os.statvfs(drive) if hasattr(os, 'statvfs') else None
                    drive_info = {
                        "drive": letter,
                        "path": drive,
                        "type": "固定磁碟"
                    }
                    drives.append(drive_info)
                except:
                    # 無法讀取的磁碟機，可能是 CD-ROM 或其他
                    drives.append({
                        "drive": letter,
                        "path": drive,
                        "type": "其他"
                    })
        
        return {
            "success": True,
            "drives": drives,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取磁碟機列表時發生錯誤: {str(e)}")

def _format_size(size_bytes: int) -> str:
    """格式化檔案大小為可讀格式"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.2f} {size_names[i]}"

@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "success": False,
            "error": "找不到請求的資源",
            "detail": str(exc.detail) if hasattr(exc, 'detail') else "Not Found",
            "timestamp": datetime.now().isoformat()
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "內部伺服器錯誤",
            "detail": str(exc.detail) if hasattr(exc, 'detail') else "Internal Server Error",
            "timestamp": datetime.now().isoformat()
        }
    )

def start_server(host: str = "127.0.0.1", port: int = 8000):
    """啟動 FastAPI 伺服器"""
    print(f"正在啟動 FastAPI 伺服器於 http://{host}:{port}")
    print("API 文檔位於 http://127.0.0.1:8000/docs")
    uvicorn.run(app, host=host, port=port, log_level="info")

if __name__ == "__main__":
    start_server()