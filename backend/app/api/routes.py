import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from pydantic import ValidationError

from src.models import GenerationTask, Segment

from ..core.security import require_auth
from ..schemas.task import Storyboard
from ..schemas.api import (
    StoryboardSummary,
    SegmentOut,
    SegmentUpdate,
    RunCreate,
    RunOut,
    TaskOut,
    ProviderOut,
    ProviderCapabilities,
    ProviderUpdate,
    ModelOut,
    ModelAdminOut,
    ModelUpdate,
    ModelProviderMapUpdate,
    PaginatedStoryboards,
    PaginatedSegments,
    PaginatedRuns,
    PaginatedTasks,
    PaginatedProviders,
    PaginatedModels,
    PaginatedAdminModels,
    ClientEventBatchIn,
    ClientEventBatchOut,
)
from ..services.store import STORE
from ..services.runner import RUNNER
from ..services.client_events import record_client_events

router = APIRouter(dependencies=[Depends(require_auth)])

UPLOAD_DIR = Path("backend/uploads")
OUTPUT_DIR = Path("backend/output")
ALLOWED_DURATIONS = {4, 8, 10, 12, 15, 25}
ALLOWED_RESOLUTIONS = {"horizontal", "vertical"}
MAX_PRIORITY = 100
MAX_WEIGHT = 100


def _error(status_code: int, code: str, message: str, details: Optional[Dict[str, Any]] = None):
    raise HTTPException(
        status_code=status_code,
        detail={"code": code, "message": message, "details": details},
    )


def _paginate(items: List[Dict[str, Any]], page: int, page_size: int):
    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    return items[start:end], total


def _sort_items(items: List[Dict[str, Any]], sort: Optional[str], order: str):
    if not sort:
        return items
    reverse = order == "desc"
    return sorted(items, key=lambda item: item.get(sort), reverse=reverse)


def _validate_provider_updates(updates: Dict[str, Any]) -> None:
    display_name = updates.get("display_name")
    if display_name is not None and not str(display_name).strip():
        _error(400, "validation_error", "display_name cannot be empty")

    priority = updates.get("priority")
    if priority is not None:
        if priority < 1 or priority > MAX_PRIORITY:
            _error(400, "validation_error", f"priority must be between 1 and {MAX_PRIORITY}")

    weight = updates.get("weight")
    if weight is not None:
        if weight < 1 or weight > MAX_WEIGHT:
            _error(400, "validation_error", f"weight must be between 1 and {MAX_WEIGHT}")

    durations = updates.get("supported_durations")
    if durations is not None:
        if not durations:
            _error(400, "validation_error", "supported_durations cannot be empty")
        invalid = [item for item in durations if item not in ALLOWED_DURATIONS]
        if invalid:
            _error(400, "validation_error", f"unsupported durations: {invalid}")

    resolutions = updates.get("supported_resolutions")
    if resolutions is not None:
        if not resolutions:
            _error(400, "validation_error", "supported_resolutions cannot be empty")
        invalid = [item for item in resolutions if item not in ALLOWED_RESOLUTIONS]
        if invalid:
            _error(400, "validation_error", f"unsupported resolutions: {invalid}")


def _validate_model_updates(updates: Dict[str, Any]) -> None:
    display_name = updates.get("display_name")
    if display_name is not None and not str(display_name).strip():
        _error(400, "validation_error", "display_name cannot be empty")


def _validate_provider_model_ids(provider_model_ids: List[str]) -> None:
    if not provider_model_ids:
        return
    if any(not str(item).strip() for item in provider_model_ids):
        _error(400, "validation_error", "provider_model_ids cannot contain empty values")
    if len(set(provider_model_ids)) != len(provider_model_ids):
        _error(400, "validation_error", "provider_model_ids cannot contain duplicates")


@router.post("/client-events", response_model=ClientEventBatchOut, status_code=202)
def create_client_events(payload: ClientEventBatchIn):
    events = [event.model_dump(exclude_none=True) for event in payload.events]
    stored = record_client_events(events)
    return ClientEventBatchOut(count=len(stored), events=stored)


@router.get("/storyboards", response_model=PaginatedStoryboards)
def list_storyboards(
    page: int = 1,
    page_size: int = 20,
    sort: Optional[str] = None,
    order: str = "desc",
    name: Optional[str] = None,
):
    items = STORE.list_storyboards()
    if name:
        items = [item for item in items if name.lower() in item["name"].lower()]
    items = _sort_items(items, sort, order)
    page_items, total = _paginate(items, page, page_size)
    summaries = [
        StoryboardSummary(
            id=item["id"],
            name=item["name"],
            created_at=item["created_at"],
            segment_count=len(item["segment_ids"]),
        )
        for item in page_items
    ]
    return PaginatedStoryboards(items=summaries, page=page, page_size=page_size, total=total)


@router.post("/storyboards", response_model=StoryboardSummary, status_code=201)
def upload_storyboard(file: UploadFile = File(...)):
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    raw_bytes = file.file.read()
    try:
        payload = json.loads(raw_bytes.decode("utf-8"))
    except json.JSONDecodeError as exc:
        _error(400, "schema_error", "Invalid JSON", {"reason": str(exc)})

    try:
        storyboard = Storyboard(**payload)
    except ValidationError as exc:
        _error(400, "schema_error", "Invalid storyboard schema", {"errors": exc.errors()})

    file_path = UPLOAD_DIR / f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{file.filename}"
    with file_path.open("wb") as f:
        f.write(raw_bytes)

    record = STORE.create_storyboard(file.filename, storyboard.segments, str(file_path))
    return StoryboardSummary(
        id=record["id"],
        name=record["name"],
        created_at=record["created_at"],
        segment_count=len(record["segment_ids"]),
    )


@router.get("/storyboards/{storyboard_id}", response_model=StoryboardSummary)
def get_storyboard(storyboard_id: str):
    record = STORE.get_storyboard(storyboard_id)
    if not record:
        _error(404, "not_found", "Storyboard not found")
    return StoryboardSummary(
        id=record["id"],
        name=record["name"],
        created_at=record["created_at"],
        segment_count=len(record["segment_ids"]),
    )


@router.get("/storyboards/{storyboard_id}/segments", response_model=PaginatedSegments)
def list_segments(
    storyboard_id: str,
    page: int = 1,
    page_size: int = 20,
    sort: Optional[str] = None,
    order: str = "desc",
    resolution: Optional[str] = None,
    is_pro: Optional[bool] = None,
):
    record = STORE.get_storyboard(storyboard_id)
    if not record:
        _error(404, "not_found", "Storyboard not found")

    segments = STORE.list_segments(storyboard_id)
    if resolution:
        segments = [seg for seg in segments if seg.get("resolution") == resolution]
    if is_pro is not None:
        segments = [seg for seg in segments if seg.get("is_pro") == is_pro]

    segments = _sort_items(segments, sort, order)
    page_items, total = _paginate(segments, page, page_size)
    items = [SegmentOut(**item) for item in page_items]
    return PaginatedSegments(items=items, page=page, page_size=page_size, total=total)


@router.patch("/segments/{segment_id}", response_model=SegmentOut)
def update_segment(segment_id: str, updates: SegmentUpdate):
    current = STORE.get_segment(segment_id)
    if not current:
        _error(404, "not_found", "Segment not found")

    data = updates.model_dump(exclude_unset=True)
    payload = {
        "segment_index": current["segment_index"],
        "prompt_text": data.get("prompt_text", current.get("prompt_text")),
        "director_intent": data.get("director_intent", current.get("director_intent")),
        "image_url": data.get("image_url", current.get("image_url")),
        "duration_seconds": data.get("duration_seconds", current.get("duration_seconds")),
        "resolution": data.get("resolution", current.get("resolution")),
        "is_pro": data.get("is_pro", current.get("is_pro")),
        "asset": data.get("asset", current.get("asset")),
    }
    try:
        Segment(**payload)
    except ValidationError as exc:
        _error(400, "validation_error", "Invalid segment update", {"errors": exc.errors()})

    updated = STORE.update_segment(segment_id, data)
    if not updated:
        _error(404, "not_found", "Segment not found")
    return SegmentOut(**updated)


@router.post("/segments/{segment_id}/assets/start-image")
def upload_start_image(segment_id: str, file: UploadFile = File(...)):
    segment = STORE.get_segment(segment_id)
    if not segment:
        _error(404, "not_found", "Segment not found")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{segment_id}_{file.filename}"
    dest = UPLOAD_DIR / filename
    with dest.open("wb") as f:
        f.write(file.file.read())

    image_url = f"/uploads/{filename}"
    STORE.update_segment(segment_id, {"image_url": image_url})
    return {"image_url": image_url}


@router.get("/runs", response_model=PaginatedRuns)
def list_runs(
    page: int = 1,
    page_size: int = 20,
    sort: Optional[str] = None,
    order: str = "desc",
    status: Optional[str] = None,
):
    runs = STORE.list_runs()
    if status:
        runs = [run for run in runs if run.get("status") == status]
    runs = _sort_items(runs, sort, order)
    page_items, total = _paginate(runs, page, page_size)
    items = [RunOut(**item) for item in page_items]
    return PaginatedRuns(items=items, page=page, page_size=page_size, total=total)


@router.post("/runs", response_model=RunOut, status_code=201)
def create_run(payload: RunCreate):
    storyboard = STORE.get_storyboard(payload.storyboard_id)
    if not storyboard:
        _error(404, "not_found", "Storyboard not found")

    model = STORE.get_model(payload.model_id)
    if not model or not model.get("enabled"):
        _error(400, "validation_error", "Invalid model_id")

    segments = STORE.list_segments(payload.storyboard_id)
    selected_indices = _parse_range(payload.range, [s["segment_index"] for s in segments])
    segments = [seg for seg in segments if seg["segment_index"] in selected_indices]

    if payload.output_mode == "custom" and not payload.output_path:
        _error(400, "validation_error", "output_path is required for custom output_mode")

    base_output_dir = _resolve_output_dir(payload, storyboard)

    segment_jobs: List[Dict[str, Any]] = []
    task_jobs: List[Tuple[str, GenerationTask]] = []
    for seg in segments:
        segment_dir = base_output_dir / f"Segment_{seg['segment_index']}"
        for version_index in range(1, payload.gen_count + 1):
            segment_jobs.append({**seg, "version_index": version_index, "output_dir": str(segment_dir)})

    config = payload.model_dump()
    config["model_id"] = payload.model_id
    run = STORE.create_run(
        payload.storyboard_id,
        segment_jobs,
        payload.gen_count,
        config=config,
    )

    for task in STORE.list_tasks(run["id"]):
        segment = STORE.get_segment(task["segment_id"])
        if not segment:
            continue
        gen_task = _build_generation_task(task, segment, storyboard)
        task_jobs.append((task["id"], gen_task))
        STORE.update_task(
            task["id"],
            {
                "metadata_url": f"/api/v1/tasks/{task['id']}/metadata",
                "video_url": None,
            },
        )

    RUNNER.launch_run(
        run["id"],
        task_jobs,
        concurrency=payload.concurrency,
        dry_run=payload.dry_run,
        force=payload.force,
        model_id=payload.model_id,
        routing_strategy=payload.routing_strategy or "default",
    )

    return RunOut(**run)


@router.get("/runs/{run_id}", response_model=RunOut)
def get_run(run_id: str):
    run = STORE.get_run(run_id)
    if not run:
        _error(404, "not_found", "Run not found")
    return RunOut(**run)


@router.get("/runs/{run_id}/tasks", response_model=PaginatedTasks)
def list_run_tasks(
    run_id: str,
    page: int = 1,
    page_size: int = 20,
    sort: Optional[str] = None,
    order: str = "desc",
    status: Optional[str] = None,
    segment_index: Optional[int] = None,
    error_code: Optional[str] = None,
    retryable: Optional[bool] = None,
):
    run = STORE.get_run(run_id)
    if not run:
        _error(404, "not_found", "Run not found")

    tasks = STORE.list_tasks(run_id)
    if status:
        tasks = [task for task in tasks if task.get("status") == status]
    if segment_index is not None:
        tasks = [task for task in tasks if task.get("segment_index") == segment_index]
    if error_code:
        tasks = [task for task in tasks if task.get("error_code") == error_code]
    if retryable is not None:
        tasks = [task for task in tasks if task.get("retryable") == retryable]

    tasks = _sort_items(tasks, sort, order)
    page_items, total = _paginate(tasks, page, page_size)
    items = [_task_out(item) for item in page_items]
    return PaginatedTasks(items=items, page=page, page_size=page_size, total=total)


@router.get("/tasks/{task_id}", response_model=TaskOut)
def get_task(task_id: str):
    task = STORE.get_task(task_id)
    if not task:
        _error(404, "not_found", "Task not found")
    return _task_out(task)


@router.post("/tasks/{task_id}/retry", response_model=TaskOut, status_code=202)
def retry_task(task_id: str):
    task = STORE.retry_task(task_id)
    if not task:
        _error(404, "not_found", "Task not found")
    segment = STORE.get_segment(task["segment_id"])
    if not segment:
        _error(404, "not_found", "Segment not found")
    storyboard = STORE.get_storyboard(segment["storyboard_id"])
    if not storyboard:
        _error(404, "not_found", "Storyboard not found")
    run = STORE.get_run(task["run_id"])
    if not run:
        _error(404, "not_found", "Run not found")
    config = run.get("config", {})
    model_id = config.get("model_id")
    if not model_id:
        _error(400, "validation_error", "Run config missing model_id")
    routing_strategy = config.get("routing_strategy", "default")
    dry_run = bool(config.get("dry_run", False))
    force = bool(config.get("force", False))
    gen_task = _build_generation_task(task, segment, storyboard)
    STORE.update_run(run["id"], {"status": "running"})
    STORE.update_task(
        task_id,
        {
            "metadata_url": f"/api/v1/tasks/{task_id}/metadata",
            "video_url": None,
        },
    )
    RUNNER.launch_retry_task(
        run["id"],
        task_id,
        gen_task,
        model_id=model_id,
        routing_strategy=routing_strategy,
        dry_run=dry_run,
        force=force,
    )
    return _task_out(STORE.get_task(task_id) or task)


@router.get("/tasks/{task_id}/download")
def download_task(task_id: str):
    task = STORE.get_task(task_id)
    if not task:
        _error(404, "not_found", "Task not found")
    video_path = task.get("video_path")
    if video_path and Path(video_path).exists():
        return FileResponse(video_path, media_type="video/mp4")
    if task.get("video_url"):
        return RedirectResponse(url=task["video_url"])
    _error(404, "not_found", "Video not available")


@router.get("/tasks/{task_id}/metadata")
def download_metadata(task_id: str):
    task = STORE.get_task(task_id)
    if not task:
        _error(404, "not_found", "Task not found")
    metadata_path = task.get("metadata_path")
    if metadata_path and Path(metadata_path).exists():
        with Path(metadata_path).open("r", encoding="utf-8") as f:
            return JSONResponse(content=json.load(f))
    return JSONResponse(content=task)


@router.get("/providers", response_model=PaginatedProviders)
def list_providers(
    page: int = 1,
    page_size: int = 20,
    sort: Optional[str] = None,
    order: str = "desc",
    enabled: Optional[bool] = None,
):
    providers = STORE.list_providers()
    if enabled is not None:
        providers = [p for p in providers if p.get("enabled") == enabled]
    providers = _sort_items(providers, sort, order)
    page_items, total = _paginate(providers, page, page_size)
    items = [ProviderOut(**item) for item in page_items]
    return PaginatedProviders(items=items, page=page, page_size=page_size, total=total)


@router.get("/providers/{provider_id}", response_model=ProviderOut)
def get_provider(provider_id: str):
    provider = STORE.get_provider(provider_id)
    if not provider:
        _error(404, "not_found", "Provider not found")
    return ProviderOut(**provider)


@router.get("/providers/{provider_id}/capabilities", response_model=ProviderCapabilities)
def get_provider_capabilities(provider_id: str):
    provider = STORE.get_provider(provider_id)
    if not provider:
        _error(404, "not_found", "Provider not found")
    return ProviderCapabilities(
        supports_image_to_video=provider["supports_image_to_video"],
        supported_durations=provider["supported_durations"],
        supported_resolutions=provider["supported_resolutions"],
        supports_pro=provider["supports_pro"],
    )


@router.get("/models", response_model=PaginatedModels)
def list_models(
    page: int = 1,
    page_size: int = 20,
    sort: Optional[str] = None,
    order: str = "desc",
    enabled: Optional[bool] = None,
):
    models = STORE.list_models()
    if enabled is not None:
        models = [m for m in models if m.get("enabled") == enabled]
    models = _sort_items(models, sort, order)
    page_items, total = _paginate(models, page, page_size)
    items = [ModelOut(**item) for item in page_items]
    return PaginatedModels(items=items, page=page, page_size=page_size, total=total)


@router.get("/models/{model_id}", response_model=ModelOut)
def get_model(model_id: str):
    model = STORE.get_model(model_id)
    if not model:
        _error(404, "not_found", "Model not found")
    return ModelOut(**model)


@router.get("/admin/providers", response_model=PaginatedProviders)
def admin_list_providers(
    page: int = 1,
    page_size: int = 20,
    sort: Optional[str] = None,
    order: str = "desc",
    enabled: Optional[bool] = None,
):
    providers = STORE.list_providers()
    if enabled is not None:
        providers = [p for p in providers if p.get("enabled") == enabled]
    providers = _sort_items(providers, sort, order)
    page_items, total = _paginate(providers, page, page_size)
    items = [ProviderOut(**item) for item in page_items]
    return PaginatedProviders(items=items, page=page, page_size=page_size, total=total)


@router.patch("/admin/providers/{provider_id}", response_model=ProviderOut)
def update_provider(provider_id: str, payload: ProviderUpdate):
    updates = payload.model_dump(exclude_unset=True)
    _validate_provider_updates(updates)
    provider = STORE.update_provider(provider_id, updates)
    if not provider:
        _error(404, "not_found", "Provider not found")
    return ProviderOut(**provider)


@router.get("/admin/models", response_model=PaginatedAdminModels)
def admin_list_models(
    page: int = 1,
    page_size: int = 20,
    sort: Optional[str] = None,
    order: str = "desc",
    enabled: Optional[bool] = None,
):
    models = STORE.list_models()
    if enabled is not None:
        models = [m for m in models if m.get("enabled") == enabled]
    models = _sort_items(models, sort, order)
    page_items, total = _paginate(models, page, page_size)
    items = [ModelAdminOut(**item) for item in page_items]
    return PaginatedAdminModels(items=items, page=page, page_size=page_size, total=total)


@router.get("/admin/models/{model_id}", response_model=ModelAdminOut)
def admin_get_model(model_id: str):
    model = STORE.get_model(model_id)
    if not model:
        _error(404, "not_found", "Model not found")
    return ModelAdminOut(**model)


@router.patch("/admin/models/{model_id}", response_model=ModelAdminOut)
def update_model(model_id: str, payload: ModelUpdate):
    updates = payload.model_dump(exclude_unset=True)
    _validate_model_updates(updates)
    model = STORE.update_model(model_id, updates)
    if not model:
        _error(404, "not_found", "Model not found")
    return ModelAdminOut(**model)


@router.patch("/admin/models/{model_id}/providers/{provider_id}", response_model=ModelAdminOut)
def update_model_provider_map(
    model_id: str,
    provider_id: str,
    payload: ModelProviderMapUpdate,
):
    provider = STORE.get_provider(provider_id)
    if not provider:
        _error(404, "not_found", "Provider not found")
    _validate_provider_model_ids(payload.provider_model_ids)
    model = STORE.update_model_provider_map(
        model_id,
        provider_id,
        payload.provider_model_ids,
    )
    if not model:
        _error(404, "not_found", "Model not found")
    return ModelAdminOut(**model)


def _build_generation_task(task: Dict[str, Any], segment: Dict[str, Any], storyboard: Dict[str, Any]) -> GenerationTask:
    segment_payload = {
        "segment_index": segment["segment_index"],
        "prompt_text": segment["prompt_text"],
        "image_url": segment.get("image_url"),
        "asset": segment.get("asset"),
        "is_pro": segment.get("is_pro", False),
        "duration_seconds": segment.get("duration_seconds", 10),
        "resolution": segment.get("resolution", "horizontal"),
        "director_intent": segment.get("director_intent"),
    }
    segment_obj = Segment(**segment_payload)
    output_dir = Path(task["output_dir"]) if task.get("output_dir") else OUTPUT_DIR / task["run_id"]
    gen_task = GenerationTask(
        id=task["id"],
        source_file=Path(storyboard["file_path"]),
        segment=segment_obj,
        version_index=task.get("version_index", 1),
        output_dir=output_dir,
    )
    STORE.update_task(
        task["id"],
        {
            "video_path": str(output_dir / f"{gen_task.output_filename_base}_{task['id']}.mp4"),
            "metadata_path": str(output_dir / f"{gen_task.output_filename_base}_{task['id']}.json"),
            "output_dir": str(output_dir),
        },
    )
    return gen_task


def _parse_range(range_input: str, all_indices: List[int]) -> List[int]:
    if range_input.lower() == "all":
        return sorted(set(all_indices))
    selected: List[int] = []
    for part in range_input.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            try:
                start_str, end_str = part.split("-", 1)
                start, end = int(start_str), int(end_str)
                if start > end:
                    continue
                selected.extend(list(range(start, end + 1)))
            except ValueError:
                continue
        else:
            try:
                selected.append(int(part))
            except ValueError:
                continue
    valid = [idx for idx in set(selected) if idx in all_indices]
    if not valid:
        _error(400, "validation_error", "No valid segments in range")
    return sorted(valid)


def _resolve_output_dir(payload: RunCreate, storyboard: Dict[str, Any]) -> Path:
    if payload.output_mode == "custom" and payload.output_path:
        base = Path(payload.output_path) / payload.storyboard_id
        base.mkdir(parents=True, exist_ok=True)
        return base
    if payload.output_mode == "in_place":
        file_path = Path(storyboard["file_path"])
        base = file_path.parent / f"{file_path.stem}_assets"
        base.mkdir(parents=True, exist_ok=True)
        return base
    base = OUTPUT_DIR / payload.storyboard_id
    base.mkdir(parents=True, exist_ok=True)
    return base


def _task_out(task: Dict[str, Any]) -> TaskOut:
    video_url = task.get("video_url")
    if not video_url and task.get("video_path") and Path(task["video_path"]).exists():
        video_url = f"/api/v1/tasks/{task['id']}/download"
    metadata_url = task.get("metadata_url") or f"/api/v1/tasks/{task['id']}/metadata"
    return TaskOut(
        id=task["id"],
        status=task.get("status", "queued"),
        video_url=video_url,
        metadata_url=metadata_url,
        full_prompt=task.get("full_prompt"),
        error_msg=task.get("error_msg"),
        error_code=task.get("error_code"),
        retryable=task.get("retryable"),
        segment_index=task.get("segment_index"),
    )
