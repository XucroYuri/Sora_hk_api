from pathlib import Path
from typing import Optional, Protocol


class ProviderClient(Protocol):
    def create_task(
        self,
        prompt: str,
        duration: int,
        resolution: str,
        is_pro: bool,
        image_url: Optional[str] = None,
        **kwargs,
    ) -> str:
        ...

    def get_task(self, task_id: str):
        ...

    def download_video(self, task_id: str, video_url: Optional[str], dest_path: Path) -> bool:
        ...
