from pathlib import Path
from typing import Optional

from src.api_client import SoraClient
from src.downloader import download_file


class SoraHKProvider:
    def __init__(self, model_id: Optional[str] = None, provider_model_id: Optional[str] = None) -> None:
        self._client = SoraClient()
        self.model_id = model_id
        self.provider_model_id = provider_model_id

    def create_task(
        self,
        prompt: str,
        duration: int,
        resolution: str,
        is_pro: bool,
        image_url: Optional[str] = None,
        **kwargs,
    ) -> str:
        return self._client.create_task(
            prompt=prompt,
            duration=duration,
            resolution=resolution,
            is_pro=is_pro,
            image_url=image_url,
            **kwargs,
        )

    def get_task(self, task_id: str):
        return self._client.get_task(task_id)

    def download_video(self, task_id: str, video_url: Optional[str], dest_path: Path) -> bool:
        return download_file(video_url or "", dest_path)
