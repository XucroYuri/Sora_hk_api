import requests
import shutil
import logging
import errno
from pathlib import Path
from typing import Optional
from .config import settings

logger = logging.getLogger(__name__)

def download_file(url: str, dest_path: Path) -> bool:
    """
    流式下载文件，包含 IO 保护和内存优化。
    Returns True if successful, False otherwise.
    """
    if not url:
        return False

    tmp_path = dest_path.with_suffix(dest_path.suffix + ".tmp")
    
    proxies = {}
    if settings.HTTP_PROXY:
        proxies["http"] = settings.HTTP_PROXY
    if settings.HTTPS_PROXY:
        proxies["https"] = settings.HTTPS_PROXY

    try:
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        # IO Protection: Increased timeout to 300s
        with requests.get(url, stream=True, proxies=proxies, timeout=300) as r:
            r.raise_for_status()
            
            total_size = int(r.headers.get('content-length', 0))
            
            with open(tmp_path, 'wb') as f:
                # Memory Protection: Use 1MB chunks to control memory usage
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)
        
        # Verify size
        if total_size > 0:
            file_size = tmp_path.stat().st_size
            if file_size != total_size:
                logger.error(f"Download incomplete: {file_size}/{total_size} bytes")
                tmp_path.unlink(missing_ok=True)
                return False

        # Atomic move
        tmp_path.replace(dest_path)
        return True

    except OSError as e:
        if e.errno == errno.ENOSPC:
            logger.critical("磁盘空间不足! (Disk Full)")
        else:
            logger.error(f"IO Error writing file: {e}")
        
        if tmp_path.exists():
            tmp_path.unlink()
        return False

    except Exception as e:
        logger.error(f"Download failed for {url}: {e}")
        if tmp_path.exists():
            tmp_path.unlink()
        return False
