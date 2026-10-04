"""限制歸檔位置只能位於模擬 NAS 目錄內。"""
from pathlib import Path

def safe_nas_path(root, subpath, filename):
    root = Path(root).resolve()
    if not filename.strip() or filename in (".", "..") or any(c in filename for c in '/\\:'):
        raise ValueError("檔案名稱不可包含路徑或磁碟代號。")
    normalized = subpath.replace("\\", "/")
    if ":" in normalized:
        raise ValueError("分類目錄不可包含磁碟代號。")
    target = (root / normalized / filename).resolve()
    if not target.is_relative_to(root):
        raise ValueError("歸檔位置必須位於模擬 NAS 目錄內。")
    return target
