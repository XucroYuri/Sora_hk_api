import requests
import shutil
import logging
import errno
from pathlib import Path
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, RetryError
from .config import settings

logger = logging.getLogger(__name__)

@retry(
    stop=stop_after_attempt(5), 
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((requests.RequestException, OSError))
)
def _download_with_retry(url: str, tmp_path: Path):
    """
    Internal function to perform the download with retries.
    Raises exceptions to trigger tenacity.
    """
    proxies = {}
    if settings.HTTP_PROXY:
        proxies["http"] = settings.HTTP_PROXY
    if settings.HTTPS_PROXY:
        proxies["https"] = settings.HTTPS_PROXY

    # IO Protection: Use configurable timeout to protect long downloads
    with requests.get(
        url,
        stream=True,
        proxies=proxies,
        timeout=settings.DOWNLOAD_TIMEOUT_SECONDS,
    ) as r:
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
            raise IOError(f"Download incomplete: {file_size}/{total_size} bytes")

def download_file(url: str, dest_path: Path) -> bool:
    """
    流式下载文件，包含 IO 保护、内存优化和重试机制。
    Returns True if successful, False otherwise.
    """
    if not url:
        return False

    tmp_path = dest_path.with_suffix(dest_path.suffix + ".tmp")
    
    try:
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Call the retrying helper
        _download_with_retry(url, tmp_path)

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

    except (requests.RequestException, RetryError) as e:
        logger.error(f"Download failed for {url} after retries: {e}")
        if tmp_path.exists():
            tmp_path.unlink()
        return False
