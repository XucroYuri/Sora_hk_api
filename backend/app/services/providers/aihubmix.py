import mimetypes
from pathlib import Path
from typing import Any, Dict, Optional

import requests

from src.api_client import APIError, RateLimitError
from src.config import settings


_SIZE_MAP = {
    "horizontal": "1280x720",
    "vertical": "720x1280",
}
_SUPPORTED_SECONDS = {4, 8, 12}


class AIHubMixProvider:
    def __init__(self, model_id: Optional[str] = None, provider_model_id: Optional[str] = None) -> None:
        self.model_id = model_id
        self.provider_model_id = provider_model_id
        self.base_url = settings.AIHUBMIX_BASE_URL.rstrip("/")
        self._session = requests.Session()
        if settings.AIHUBMIX_API_KEY:
            self._session.headers.update({"Authorization": f"Bearer {settings.AIHUBMIX_API_KEY}"})
        if settings.HTTP_PROXY:
            self._session.proxies.update(
                {
                    "http": settings.HTTP_PROXY,
                    "https": settings.HTTPS_PROXY or settings.HTTP_PROXY,
                }
            )

    def create_task(
        self,
        prompt: str,
        duration: int,
        resolution: str,
        is_pro: bool,
        image_url: Optional[str] = None,
        **kwargs,
    ) -> str:
        if not settings.AIHUBMIX_API_KEY:
            raise APIError("AIHubMix API key not configured")

        model = self.provider_model_id or ("sora-2-pro" if is_pro else "sora-2")
        size = _SIZE_MAP.get(resolution)
        if not size:
            raise APIError(f"Unsupported resolution for AIHubMix: {resolution}")

        if duration not in _SUPPORTED_SECONDS:
            raise APIError(f"Unsupported duration for AIHubMix: {duration}")

        if image_url:
            file_path = _resolve_image_path(image_url)
            if not file_path or not file_path.exists():
                raise APIError("input_reference not available for AIHubMix")
            mime_type, _ = mimetypes.guess_type(file_path.name)
            files = {
                "prompt": (None, prompt),
                "model": (None, model),
                "size": (None, size),
                "seconds": (None, str(duration)),
                "input_reference": (
                    file_path.name,
                    file_path.open("rb"),
                    mime_type or "application/octet-stream",
                ),
            }
            try:
                data = self._request("POST", "/videos", files=files)
            finally:
                files["input_reference"][1].close()
        else:
            payload = {
                "model": model,
                "prompt": prompt,
                "size": size,
                "seconds": str(duration),
            }
            data = self._request("POST", "/videos", json=payload)

        video_id = _extract_video_id(data)
        if not video_id:
            raise APIError("AIHubMix response missing video id")
        return video_id

    def get_task(self, task_id: str):
        if not settings.AIHUBMIX_API_KEY:
            raise APIError("AIHubMix API key not configured")
        data = self._request("GET", f"/videos/{task_id}")
        status = _normalize_status(data.get("status") or data.get("state"))
        video_url = (
            data.get("video_url")
            or data.get("url")
            or data.get("output_url")
            or f"{self.base_url}/videos/{task_id}/content"
        )
        progress = data.get("progress") or data.get("percentage") or 0
        return {"status": status, "progress": progress, "video_url": video_url, "raw": data}

    def download_video(self, task_id: str, video_url: Optional[str], dest_path: Path) -> bool:
        if not settings.AIHUBMIX_API_KEY:
            raise APIError("AIHubMix API key not configured")
        url = video_url or f"{self.base_url}/videos/{task_id}/content"
        tmp_path = dest_path.with_suffix(dest_path.suffix + ".tmp")
        try:
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            with self._session.get(
                url,
                stream=True,
                timeout=settings.DOWNLOAD_TIMEOUT_SECONDS,
            ) as resp:
                if resp.status_code == 401:
                    raise APIError("AIHubMix unauthorized")
                if resp.status_code == 429:
                    raise RateLimitError("AIHubMix rate limited")
                resp.raise_for_status()
                with tmp_path.open("wb") as f:
                    for chunk in resp.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            f.write(chunk)
            tmp_path.replace(dest_path)
            return True
        except requests.RequestException as exc:
            if tmp_path.exists():
                tmp_path.unlink()
            raise APIError(str(exc)) from exc
        except OSError as exc:
            if tmp_path.exists():
                tmp_path.unlink()
            raise APIError(str(exc)) from exc

    def _request(
        self,
        method: str,
        endpoint: str,
        json: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        try:
            response = self._session.request(
                method,
                url,
                json=json,
                files=files,
                timeout=settings.API_REQUEST_TIMEOUT_SECONDS,
            )
            if response.status_code == 401:
                raise APIError("AIHubMix unauthorized")
            if response.status_code == 429:
                raise RateLimitError("AIHubMix rate limited")
            response.raise_for_status()
            try:
                return response.json()
            except ValueError as exc:
                raise APIError("AIHubMix returned non-JSON response") from exc
        except requests.RequestException as exc:
            raise APIError(str(exc)) from exc


def _normalize_status(status: Optional[str]) -> str:
    if not status:
        return "running"
    lowered = status.lower()
    if lowered in {"completed", "succeeded", "success", "done"}:
        return "completed"
    if lowered in {"failed", "error", "canceled", "cancelled"}:
        return "failed"
    return "running"


def _extract_video_id(data: Dict[str, Any]) -> Optional[str]:
    for key in ("id", "video_id", "task_id"):
        if data.get(key):
            return data.get(key)
    nested = data.get("data") if isinstance(data.get("data"), dict) else None
    if nested:
        for key in ("id", "video_id", "task_id"):
            if nested.get(key):
                return nested.get(key)
    return None


def _resolve_image_path(image_url: str) -> Optional[Path]:
    if image_url.startswith("/uploads/"):
        filename = image_url.split("/uploads/", 1)[1]
        return Path("backend/uploads") / filename
    candidate = Path(image_url)
    if candidate.exists():
        return candidate
    return None
