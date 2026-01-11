import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.models import GenerationTask
from src.worker import process_task

from .store import STORE
from .providers.registry import get_provider_client, select_provider_candidates
from .error_policy import classify_error


class RunManager:
    def __init__(self) -> None:
        self._threads: Dict[str, threading.Thread] = {}

    def launch_run(
        self,
        run_id: str,
        task_jobs: List[Tuple[str, GenerationTask]],
        concurrency: int,
        dry_run: bool,
        force: bool,
        model_id: str,
        routing_strategy: str,
    ) -> None:
        thread = threading.Thread(
            target=self._execute_run,
            args=(run_id, task_jobs, concurrency, dry_run, force, model_id, routing_strategy),
            daemon=True,
        )
        self._threads[run_id] = thread
        thread.start()

    def _execute_run(
        self,
        run_id: str,
        task_jobs: List[Tuple[str, GenerationTask]],
        concurrency: int,
        dry_run: bool,
        force: bool,
        model_id: str,
        routing_strategy: str,
    ) -> None:
        selections: Dict[str, List[Tuple[str, str]]] = {}
        failures: Dict[str, str] = {}
        for task_id, gen_task in task_jobs:
            try:
                selections[task_id] = select_provider_candidates(
                    model_id,
                    routing_strategy=routing_strategy,
                    required_durations=[gen_task.segment.duration_seconds],
                    required_resolutions=[gen_task.segment.resolution],
                    requires_pro=gen_task.segment.is_pro,
                    requires_image=bool(gen_task.segment.image_url),
                )
            except ValueError as exc:
                selections[task_id] = []
                failures[task_id] = str(exc)

        chosen = {candidates[0] for candidates in selections.values() if candidates}
        if len(chosen) == 1 and not failures:
            provider_id, provider_model_id = next(iter(chosen))
            STORE.update_run(run_id, {"provider_id": provider_id, "provider_model_id": provider_model_id})
        else:
            STORE.update_run(run_id, {"provider_id": None, "provider_model_id": None})

        def run_one(task_id: str, gen_task: GenerationTask) -> Dict[str, Any]:
            candidates = selections.get(task_id) or []
            return self._run_task(
                task_id,
                gen_task,
                model_id,
                routing_strategy,
                candidates=candidates,
                failure_message=failures.get(task_id),
                dry_run=dry_run,
                force=force,
            )

        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = {
                executor.submit(run_one, task_id, gen_task): task_id
                for task_id, gen_task in task_jobs
            }

            for future in as_completed(futures):
                task_id = futures[future]
                try:
                    result = future.result()
                except Exception as exc:
                    STORE.update_task(task_id, {"status": "failed", "error_msg": str(exc)})
                    result = {"status": "failed"}

                STORE.increment_run_counts(run_id, result["status"])

        run = STORE.get_run(run_id)
        if not run:
            return
        final_status = "completed"
        if run.get("failed", 0) > 0 or run.get("download_failed", 0) > 0:
            final_status = "failed"
        STORE.update_run(run_id, {"status": final_status})

    def launch_retry_task(
        self,
        run_id: str,
        task_id: str,
        gen_task: GenerationTask,
        model_id: str,
        routing_strategy: str,
        dry_run: bool,
        force: bool,
    ) -> None:
        thread = threading.Thread(
            target=self._execute_retry_task,
            args=(run_id, task_id, gen_task, model_id, routing_strategy, dry_run, force),
            daemon=True,
        )
        self._threads[f"retry-{task_id}"] = thread
        thread.start()

    def _execute_retry_task(
        self,
        run_id: str,
        task_id: str,
        gen_task: GenerationTask,
        model_id: str,
        routing_strategy: str,
        dry_run: bool,
        force: bool,
    ) -> None:
        try:
            candidates = select_provider_candidates(
                model_id,
                routing_strategy=routing_strategy,
                required_durations=[gen_task.segment.duration_seconds],
                required_resolutions=[gen_task.segment.resolution],
                requires_pro=gen_task.segment.is_pro,
                requires_image=bool(gen_task.segment.image_url),
            )
        except ValueError:
            candidates = []

        self._run_task(
            task_id,
            gen_task,
            model_id,
            routing_strategy,
            candidates=candidates,
            failure_message="no enabled provider for task",
            dry_run=dry_run,
            force=force,
        )
        STORE.recount_run(run_id)

    def _run_task(
        self,
        task_id: str,
        gen_task: GenerationTask,
        model_id: str,
        routing_strategy: str,
        candidates: List[Tuple[str, str]],
        failure_message: Optional[str],
        dry_run: bool,
        force: bool,
    ) -> Dict[str, Any]:
        if not candidates:
            error_msg = failure_message or "no enabled provider for task"
            STORE.update_task(
                task_id,
                {
                    "status": "failed",
                    "error_msg": error_msg,
                    "error_code": "no_provider",
                    "retryable": False,
                },
            )
            return {"status": "failed"}
        last_updates: Dict[str, Any] = {}
        for index, (provider_id, provider_model_id) in enumerate(candidates):
            STORE.update_task(
                task_id,
                {
                    "status": "running",
                    "provider_id": provider_id,
                    "provider_model_id": provider_model_id,
                },
            )
            client = get_provider_client(
                provider_id,
                model_id=model_id,
                provider_model_id=provider_model_id,
            )
            result = process_task(gen_task, client, dry_run=dry_run, force=force)

            meta_path = gen_task.output_dir / f"{gen_task.output_filename_base}_{gen_task.id}.json"
            video_path = gen_task.output_dir / f"{gen_task.output_filename_base}_{gen_task.id}.mp4"
            metadata = _load_metadata(meta_path)
            local_status = metadata.get("local_status") if metadata else None

            status = _map_status(result, local_status)
            error_msg = metadata.get("error_msg") if metadata else None
            error_code = None
            retryable = None
            if status != "completed":
                if local_status == "download_failed":
                    error_code = "download_failed"
                    retryable = False
                else:
                    error_code, retryable = classify_error(error_msg)
            last_updates = {
                "status": status,
                "metadata_path": str(meta_path),
                "video_path": str(video_path),
                "full_prompt": metadata.get("full_prompt") if metadata else None,
                "error_msg": error_msg,
                "video_url": metadata.get("video_url") if metadata else None,
                "error_code": error_code,
                "retryable": retryable,
            }
            _persist_metadata(meta_path, {"error_code": error_code, "retryable": retryable})
            if (
                routing_strategy == "failover"
                and status == "failed"
                and local_status != "download_failed"
                and retryable
            ):
                if index < len(candidates) - 1:
                    continue
            STORE.update_task(task_id, last_updates)
            return {"status": status}

        STORE.update_task(task_id, last_updates or {"status": "failed"})
        return {"status": (last_updates.get("status") if last_updates else "failed")}


def _map_status(result: str, local_status: Optional[str]) -> str:
    if local_status == "download_failed":
        return "download_failed"
    if result in {"completed", "skipped", "dry_run"}:
        return "completed"
    return "failed"


def _load_metadata(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


def _persist_metadata(path: Path, updates: Dict[str, Any]) -> None:
    if not path.exists():
        return
    metadata = _load_metadata(path)
    metadata.update({k: v for k, v in updates.items() if v is not None})
    try:
        with path.open("w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
    except OSError:
        return


RUNNER = RunManager()
