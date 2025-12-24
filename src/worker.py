import time
import json
import logging
import random
import gc
import re
from pathlib import Path
from typing import Dict, Any, Literal
from .models import GenerationTask
from .api_client import SoraClient, APIError, RateLimitError
from .downloader import download_file
from .concurrency import concurrency_controller

logger = logging.getLogger(__name__)

# Polling configuration
# 视频生成通常较慢，无需通过指数退避进行频繁探测
POLL_INITIAL_WAIT = 20  
POLL_INTERVAL = 10      
MAX_POLL_TIME = 2100     # 35分钟 (覆盖 Pro 模式最长生成时间)

def construct_enhanced_prompt(segment) -> str:
    """
    Constructs a rich prompt by merging prompt_text with asset info and director intent.
    Ensures no narrative context is lost when sending to the API.
    Also enforces @characterid format with trailing space.
    """
    final_prompt = segment.prompt_text.strip()
    
    # 1. Asset Integration (Scene, Characters, Props)
    asset_info = []
    if segment.asset:
        if segment.asset.scene:
            asset_info.append(f"Scene: {segment.asset.scene}")
        
        if segment.asset.characters:
            chars_str = ", ".join(segment.asset.characters)
            asset_info.append(f"Characters: {chars_str}")
            
        if segment.asset.props:
            props_str = ", ".join(segment.asset.props)
            asset_info.append(f"Props: {props_str}")
            
    if asset_info:
        final_prompt += f" [{ ' | '.join(asset_info) }]"

    if segment.director_intent:
        final_prompt += f" (Director Note: {segment.director_intent})"

    # 3. CRITICAL FIX: Ensure @characterid is followed by a space
    # Regex explanation: 
    # Find '@' followed by word characters (\w+), 
    # but ONLY if not already followed by a space.
    # We replace it with the match + a space.
    final_prompt = re.sub(r'(@\w+)(?!\s)', r'\1 ', final_prompt)
    
    # Clean up any potential double spaces created by the above (safety)
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
        # Memory Protection
        gc.collect()

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

    try:
        # 3. Jitter
        time.sleep(random.uniform(0.5, 3.0))
        
        # 4. Submit Task
        logger.info(f"Submitting task {task.id}")
        try:
            task_id = client.create_task(
                prompt=full_prompt,  # Use the enhanced prompt
                duration=task.segment.duration_seconds,
                resolution=task.segment.resolution,
                is_pro=task.segment.is_pro,
                image_url=task.segment.image_url
            )
            # Report success to reset consecutive error count for Circuit Breaker
            if concurrency_controller:
                concurrency_controller.report_success()
                
        except (RateLimitError, APIError) as e:
            # Report error to trigger potential Safe Mode
            logger.error(f"Task {task.id} submission failed: {e}")
            if concurrency_controller:
                concurrency_controller.report_error()
            return "failed"
        
        # 5. Polling
        time.sleep(POLL_INITIAL_WAIT)
        start_time = time.time()
        
        while time.time() - start_time < MAX_POLL_TIME:
            try:
                status_data = client.get_task(task_id)
            except Exception as e:
                # Polling errors usually don't need to trigger global safe mode unless consistent
                logger.warning(f"Polling warning for {task.id}: {e}")
                time.sleep(POLL_INTERVAL)
                continue

            status = status_data.get("status")
            progress = status_data.get("progress", 0)
            
            logger.debug(f"Task {task.id} status: {status} ({progress}%)")
            
            if status == "completed":
                video_url = status_data.get("video_url")
                task.output_dir.mkdir(parents=True, exist_ok=True)
                
                with open(meta_path, 'w', encoding='utf-8') as f:
                    json.dump(status_data, f, indent=2, ensure_ascii=False)
                
                if download_file(video_url, video_path):
                    logger.info(f"Task {task.id} completed successfully.")
                    return "completed"
                else:
                    logger.error(f"Task {task.id} download failed.")
                    return "failed"
            
            elif status == "failed":
                error_msg = status_data.get("error_msg", "Unknown error")
                logger.error(f"Task {task.id} failed API side: {error_msg}")
                task.output_dir.mkdir(parents=True, exist_ok=True)
                with open(meta_path, 'w', encoding='utf-8') as f:
                    json.dump(status_data, f, indent=2, ensure_ascii=False)
                return "failed"
            
            time.sleep(POLL_INTERVAL)
            
        logger.error(f"Task {task.id} timed out after {MAX_POLL_TIME}s.")
        return "failed"

    except Exception as e:
        logger.exception(f"Unexpected error in task {task.id}: {e}")
        return "failed"