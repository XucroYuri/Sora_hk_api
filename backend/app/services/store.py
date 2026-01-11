import threading
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

from pydantic import BaseModel

from ..schemas.task import Segment


class InMemoryStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.storyboards: Dict[str, Dict[str, Any]] = {}
        self.segments: Dict[str, Dict[str, Any]] = {}
        self.runs: Dict[str, Dict[str, Any]] = {}
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.providers: Dict[str, Dict[str, Any]] = {}
        self.models: Dict[str, Dict[str, Any]] = {}
        self._seed_providers()
        self._seed_models()

    def _seed_providers(self) -> None:
        self.providers = {
            "sora_hk": {
                "id": "sora_hk",
                "display_name": "Sora.hk",
                "enabled": True,
                "priority": 10,
                "weight": 1,
                "supports_image_to_video": True,
                "supported_durations": [10, 15, 25],
                "supported_resolutions": ["horizontal", "vertical"],
                "supports_pro": True,
            },
            "openai": {
                "id": "openai",
                "display_name": "OpenAI",
                "enabled": False,
                "priority": 20,
                "weight": 1,
                "supports_image_to_video": True,
                "supported_durations": [4, 8, 12],
                "supported_resolutions": ["horizontal", "vertical"],
                "supports_pro": True,
            },
            "aihubmix": {
                "id": "aihubmix",
                "display_name": "AI Hub Mix",
                "enabled": False,
                "priority": 30,
                "weight": 1,
                "supports_image_to_video": True,
                "supported_durations": [4, 8, 12],
                "supported_resolutions": ["horizontal", "vertical"],
                "supports_pro": True,
            },
        }

    def _seed_models(self) -> None:
        self.models = {
            "sora2": {
                "id": "sora2",
                "display_name": "Sora2",
                "description": "Logical model for standard generation",
                "enabled": True,
                "provider_map": {
                    "sora_hk": ["sora2"],
                    "openai": ["sora-2", "sora-2-2025-12-08", "sora-2-2025-10-06"],
                    "aihubmix": ["sora-2", "web-sora-2"],
                },
            },
            "sora2pro": {
                "id": "sora2pro",
                "display_name": "Sora2 Pro",
                "description": "Logical model for pro generation",
                "enabled": True,
                "provider_map": {
                    "sora_hk": ["sora2-pro"],
                    "openai": ["sora-2-pro", "sora-2-pro-2025-10-06"],
                    "aihubmix": ["sora-2-pro", "web-sora-2-pro"],
                },
            },
        }

    def create_storyboard(self, name: str, segments: List[Segment], file_path: str) -> Dict[str, Any]:
        storyboard_id = uuid.uuid4().hex
        created_at = datetime.utcnow()
        segment_ids: List[str] = []
        with self._lock:
            for segment in segments:
                segment_id = uuid.uuid4().hex
                segment_ids.append(segment_id)
                self.segments[segment_id] = {
                    "id": segment_id,
                    "storyboard_id": storyboard_id,
                    "segment_index": segment.segment_index,
                    "prompt_text": segment.prompt_text,
                    "director_intent": segment.director_intent,
                    "image_url": segment.image_url,
                    "duration_seconds": segment.duration_seconds,
                    "resolution": segment.resolution,
                    "is_pro": segment.is_pro,
                    "asset": segment.asset.model_dump() if segment.asset else None,
                }

        record = {
            "id": storyboard_id,
            "name": name,
            "created_at": created_at,
            "segment_ids": segment_ids,
            "file_path": file_path,
        }
        with self._lock:
            self.storyboards[storyboard_id] = record
        return record

    def list_storyboards(self) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self.storyboards.values())

    def get_storyboard(self, storyboard_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self.storyboards.get(storyboard_id)

    def list_segments(self, storyboard_id: str) -> List[Dict[str, Any]]:
        with self._lock:
            return [
                seg
                for seg in self.segments.values()
                if seg.get("storyboard_id") == storyboard_id
            ]

    def get_segment(self, segment_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self.segments.get(segment_id)

    def update_segment(self, segment_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        with self._lock:
            segment = self.segments.get(segment_id)
            if not segment:
                return None
            for key, value in updates.items():
                if value is not None:
                    if key == "asset" and isinstance(value, BaseModel):
                        segment[key] = value.model_dump()
                    else:
                        segment[key] = value
            return segment

    def create_run(
        self,
        storyboard_id: str,
        segments: List[Dict[str, Any]],
        gen_count: int,
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        run_id = uuid.uuid4().hex
        created_at = datetime.utcnow()
        tasks: List[str] = []

        with self._lock:
            for segment in segments:
                task_id = uuid.uuid4().hex
                tasks.append(task_id)
                self.tasks[task_id] = {
                    "id": task_id,
                    "run_id": run_id,
                    "segment_id": segment["id"],
                    "segment_index": segment["segment_index"],
                    "version_index": segment.get("version_index", 1),
                    "output_dir": segment.get("output_dir"),
                    "status": "queued",
                    "video_url": None,
                    "metadata_url": None,
                    "full_prompt": None,
                    "error_msg": None,
                    "error_code": None,
                    "retryable": None,
                    "video_path": None,
                    "metadata_path": None,
                    "provider_id": None,
                    "provider_model_id": None,
                }

            run = {
                "id": run_id,
                "status": "running",
                "total_tasks": len(tasks),
                "completed": 0,
                "failed": 0,
                "download_failed": 0,
                "created_at": created_at,
                "task_ids": tasks,
                "config": config,
                "provider_id": None,
                "provider_model_id": None,
            }
            self.runs[run_id] = run
        return run

    def list_runs(self) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self.runs.values())

    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self.runs.get(run_id)

    def list_tasks(self, run_id: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._lock:
            if not run_id:
                return list(self.tasks.values())
            return [task for task in self.tasks.values() if task.get("run_id") == run_id]

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self.tasks.get(task_id)

    def update_task(self, task_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        with self._lock:
            task = self.tasks.get(task_id)
            if not task:
                return None
            task.update(updates)
            return task

    def update_run(self, run_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        with self._lock:
            run = self.runs.get(run_id)
            if not run:
                return None
            run.update(updates)
            return run

    def increment_run_counts(self, run_id: str, status: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            run = self.runs.get(run_id)
            if not run:
                return None
            if status == "completed":
                run["completed"] = run.get("completed", 0) + 1
            elif status == "download_failed":
                run["download_failed"] = run.get("download_failed", 0) + 1
            else:
                run["failed"] = run.get("failed", 0) + 1
            return run

    def recount_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            run = self.runs.get(run_id)
            if not run:
                return None
            tasks = [task for task in self.tasks.values() if task.get("run_id") == run_id]
            completed = sum(1 for task in tasks if task.get("status") == "completed")
            failed = sum(1 for task in tasks if task.get("status") == "failed")
            download_failed = sum(1 for task in tasks if task.get("status") == "download_failed")
            run["completed"] = completed
            run["failed"] = failed
            run["download_failed"] = download_failed
            if any(task.get("status") in {"queued", "running"} for task in tasks):
                run["status"] = "running"
            elif failed > 0 or download_failed > 0:
                run["status"] = "failed"
            else:
                run["status"] = "completed"
            return run

    def retry_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            task = self.tasks.get(task_id)
            if not task:
                return None
            task["status"] = "queued"
            task["error_msg"] = None
            task["error_code"] = None
            task["retryable"] = None
            return task

    def list_providers(self) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self.providers.values())

    def get_provider(self, provider_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self.providers.get(provider_id)

    def update_provider(self, provider_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        with self._lock:
            provider = self.providers.get(provider_id)
            if not provider:
                return None
            provider.update(updates)
            return provider

    def list_models(self) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self.models.values())

    def get_model(self, model_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self.models.get(model_id)

    def update_model(self, model_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        with self._lock:
            model = self.models.get(model_id)
            if not model:
                return None
            model.update(updates)
            return model

    def update_model_provider_map(
        self,
        model_id: str,
        provider_id: str,
        provider_model_ids: List[str],
    ) -> Optional[Dict[str, Any]]:
        with self._lock:
            model = self.models.get(model_id)
            if not model:
                return None
            provider_map = model.setdefault("provider_map", {})
            if provider_model_ids:
                provider_map[provider_id] = provider_model_ids
            else:
                provider_map.pop(provider_id, None)
            return model


STORE = InMemoryStore()
