import time
import json
import logging
import random
import gc
import re
from pathlib import Path
from typing import Dict, Any, Literal, Optional
from .models import GenerationTask
from .api_client import SoraClient, APIError, RateLimitError
from .downloader import download_file
from .concurrency import concurrency_controller
from .config import settings

logger = logging.getLogger(__name__)

def _write_metadata(meta_path: Path, payload: Dict[str, Any]) -> None:
    try:
        meta_path.parent.mkdir(parents=True, exist_ok=True)
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
    except OSError as e:
        logger.error(f"Failed to write metadata {meta_path}: {e}")

def _build_metadata(
    task: GenerationTask,
    full_prompt: str,
    task_id: Optional[str] = None,
    status_data: Optional[Dict[str, Any]] = None,
    local_status: Optional[str] = None,
    error_msg: Optional[str] = None,
) -> Dict[str, Any]:
    data: Dict[str, Any] = {}
    if status_data:
        data.update(status_data)
    if task_id:
        data["task_id"] = task_id
    if local_status:
        data["local_status"] = local_status
    if error_msg:
        data["error_msg"] = error_msg
    data["full_prompt"] = full_prompt
    data["local_task_id"] = task.id
    data["source_file"] = str(task.source_file)
    data["segment_index"] = task.segment.segment_index
    data["version_index"] = task.version_index
    return data


def _download_video(client: Any, task_id: str, video_url: Optional[str], dest_path: Path) -> bool:
    if hasattr(client, "download_video"):
        try:
            return client.download_video(task_id=task_id, video_url=video_url, dest_path=dest_path)
        except Exception as exc:
            logger.error(f"Download failed for {task_id}: {exc}")
            return False
    if not video_url:
        return False
    return download_file(video_url, dest_path)

def _inject_character_ids(text: str, characters: list) -> str:
    """
    Replaces character names with their IDs in the text, avoiding quoted dialogue.
    Enforces a trailing space after the ID.
    
    Smart Strict Mode:
    - If the text uses explicit brackets for ANY known character (e.g. "[Alice]"), 
      we assume strict V2 formatting. In this mode, ONLY bracketed names are replaced.
      Plain names (e.g. "Alice") are treated as normal text (distinction rule).
    - If NO brackets are found for known characters, we fall back to Legacy Mode
      (replacing plain names).
    """
    if not characters:
        return text

    # Sort by name length (descending)
    sorted_chars = sorted(characters, key=lambda x: len(x.name), reverse=True)
    
    # 1. Detect Mode
    # Check if any character appears as "[Name]" in the text
    strict_mode = False
    for char in sorted_chars:
        # Simple check: "[Name]" in text
        # (Technically we should check if it's outside quotes, but a quick check usually suffices for mode detection)
        if f"[{char.name}]" in text:
            strict_mode = True
            break
            
    # logger.debug(f"ID Injection Mode: {'Strict ([Name])' if strict_mode else 'Legacy (Name)'}")

    for char in sorted_chars:
        if not char.id:
            continue
            
        name = char.name
        char_id = char.id
        replacement = f"{char_id} "
        esc_name = re.escape(name)
        
        # Regex Construction based on Mode
        if strict_mode:
            # STRICT: Match quotes (ignore) OR [Name] (replace)
            # We DO NOT match plain Name
            pattern = r'("[^"]*"|“[^”]*”)|(\[' + esc_name + r'\])'
        else:
            # LEGACY: Match quotes (ignore) OR [Name] (replace) OR Name (replace)
            # (Keeping [Name] support in legacy just in case)
            pattern = r'("[^"]*"|“[^”]*”)|(\[' + esc_name + r'\])|(' + esc_name + r')'
        
        def repl(m):
            # Group 1 is always quotes -> keep
            if m.group(1):
                return m.group(1)
            # Any other match -> replace
            return replacement
            
        text = re.sub(pattern, repl, text)
        
    return text

def construct_enhanced_prompt(segment) -> str:
    """
    Constructs a rich prompt by merging prompt_text with asset info and director intent.
    Now uses IN-PLACE replacement for Character IDs instead of appending.
    """
    asset = segment.asset

    # 1. Apply Character ID Injection (Name -> @ID)
    # This serves as the UNIQUE anchor for characters.
    characters = asset.characters if asset else []
    final_prompt = _inject_character_ids(segment.prompt_text.strip(), characters)
    
    # 2. Asset Integration (Scene, Props) - Characters are now handled in-text
    asset_info = []
    if asset:
        if asset.scene:
            asset_info.append(f"Scene: {asset.scene}")
        
        # We NO LONGER append "Characters: ..." list to avoid redundancy/confusion
        # The @ID in the text is the primary trigger.
            
        if asset.props:
            props_str = ", ".join(asset.props)
            asset_info.append(f"Props: {props_str}")
            
    if asset_info:
        final_prompt += f" [{ ' | '.join(asset_info) }]"

    if segment.director_intent:
        final_prompt += f" (Director Note: {segment.director_intent})"

    # 3. Clean up formatting
    # MANDATORY SPACE ENFORCEMENT: 
    # Ensure every @ID is followed by a space, even before punctuation or CJK characters.
    # We add a space BEFORE and AFTER the @ID to ensure absolute separation from all surrounding characters.
    final_prompt = re.sub(r'(@[a-zA-Z0-9_]+)', r' \1 ', final_prompt)
    
    # Collapse multiple spaces
    final_prompt = re.sub(r'\s+', ' ', final_prompt)
        
    return final_prompt.strip()

def process_task(
    task: GenerationTask, 
    client: SoraClient, 
    dry_run: bool = False, 
    force: bool = False
) -> Literal["completed", "failed", "skipped", "dry_run"]:
    """
    执行单个视频生成的完整生命周期，受自适应并发控制器管理。
    """
    
    # 0. Concurrency Control (Before doing anything)
    # This blocks if the system is in Safe Mode and full
    if concurrency_controller:
        concurrency_controller.acquire()
    
    try:
        return _process_task_internal(task, client, dry_run, force)
    finally:
        # Always release the slot
        if concurrency_controller:
            concurrency_controller.release()

def _process_task_internal(
    task: GenerationTask, 
    client: SoraClient, 
    dry_run: bool = False, 
    force: bool = False
) -> str:
    # Define output paths
    video_path = task.output_dir / f"{task.output_filename_base}_{task.id}.mp4"
    meta_path = task.output_dir / f"{task.output_filename_base}_{task.id}.json"

    # 1. Skip Logic
    if not force and video_path.exists() and video_path.stat().st_size > 0:
        logger.info(f"Skipping task {task.id} - file exists.")
        return "skipped"

    # 1.5 Construct Full Prompt (Merge metadata into prompt)
    full_prompt = construct_enhanced_prompt(task.segment)

    # 2. Dry Run
    if dry_run:
        logger.info(f"[DRY RUN] Final Prompt: {full_prompt[:100]}...")
        return "dry_run"

    # RETRY LOOP
    max_retries = 3
    last_error: Optional[str] = None
    last_task_id: Optional[str] = None
    for attempt in range(1, max_retries + 1):
        try:
            if attempt > 1:
                logger.info(f"Task {task.id} - Retry Attempt {attempt}/{max_retries}...")
                time.sleep(random.uniform(2.0, 5.0)) # Backoff

            # 3. Jitter
            time.sleep(random.uniform(0.5, 3.0))
            
            # 4. Submit Task
            logger.info(f"Submitting task {task.id}")
            try:
                task_id = client.create_task(
                    prompt=full_prompt,
                    duration=task.segment.duration_seconds,
                    resolution=task.segment.resolution,
                    is_pro=task.segment.is_pro,
                    image_url=task.segment.image_url
                )
                last_task_id = task_id
                if concurrency_controller:
                    concurrency_controller.report_success()
                    
            except (RateLimitError, APIError) as e:
                logger.error(f"Task {task.id} submission failed: {e}")
                last_error = f"submission failed: {e}"
                if concurrency_controller:
                    concurrency_controller.report_error()
                # If submission failed, retry immediately (next loop)
                continue
            
            # 5. Polling
            time.sleep(settings.POLL_INITIAL_WAIT_SECONDS)
            start_time = time.time()
            
            task_success = False
            while time.time() - start_time < settings.MAX_POLL_TIME:
                try:
                    status_data = client.get_task(task_id)
                except (APIError, RateLimitError) as e:
                    logger.warning(f"Polling warning for {task.id}: {e}")
                    time.sleep(settings.POLL_INTERVAL_SECONDS)
                    continue

                status = status_data.get("status")
                progress = status_data.get("progress", 0)
                
                logger.debug(f"Task {task.id} status: {status} ({progress}%)")
                
                if status == "completed":
                    video_url = status_data.get("video_url")
                    task.output_dir.mkdir(parents=True, exist_ok=True)
                    metadata = _build_metadata(
                        task,
                        full_prompt,
                        task_id=task_id,
                        status_data=status_data,
                        local_status="completed",
                    )

                    if not video_url:
                        metadata["local_status"] = "failed"
                        metadata["error_msg"] = "missing video_url in API response"
                        _write_metadata(meta_path, metadata)
                        logger.error(f"Task {task.id} completed without video_url.")
                        return "failed"

                    if _download_video(client, task_id, video_url, video_path):
                        metadata["download_status"] = "success"
                        _write_metadata(meta_path, metadata)
                        logger.info(f"Task {task.id} completed successfully.")
                        return "completed"

                    # CRITICAL FIX: Do not retry generation if download fails.
                    # The video is generated and the URL is saved in the JSON metadata.
                    metadata["local_status"] = "download_failed"
                    metadata["download_status"] = "failed"
                    metadata["error_msg"] = f"download failed for {video_url}"
                    _write_metadata(meta_path, metadata)
                    logger.error(f"Task {task.id} download failed after retries. Video URL saved in metadata.")
                    logger.error(f"Manual download required: {video_url}")
                    return "failed"
                
                elif status == "failed":
                    error_msg = status_data.get("error_msg", "Unknown error")
                    logger.error(f"Task {task.id} failed API side: {error_msg}")
                    last_error = f"api failed: {error_msg}"
                    # API failed -> Break polling loop to retry submission
                    break
                
                time.sleep(settings.POLL_INTERVAL_SECONDS)
            else:
                logger.error(f"Task {task.id} timed out after {settings.MAX_POLL_TIME}s.")
                last_error = f"timeout after {settings.MAX_POLL_TIME}s"
                # Timeout -> Retry
            
        except (APIError, RateLimitError) as e:
            logger.error(f"Task {task.id} API error: {e}")
            last_error = f"api error: {e}"
            # Known API error -> Retry
        except Exception as e:
            logger.exception(f"Unexpected error in task {task.id}: {e}")
            raise

    metadata = _build_metadata(
        task,
        full_prompt,
        task_id=last_task_id,
        local_status="failed",
        error_msg=last_error or "unknown error",
    )
    _write_metadata(meta_path, metadata)
    return "failed"
