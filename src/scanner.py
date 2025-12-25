import json
import logging
from pathlib import Path
from typing import List, Literal
from .models import Storyboard, GenerationTask
from .config import settings
from .asset_manager import AssetManager

logger = logging.getLogger(__name__)

def discover_tasks(
    input_dir: Path, 
    output_mode: Literal["centralized", "in_place"] = "centralized",
    override_output_dir: Path = None,
    gen_count: int = settings.GEN_COUNT_PER_SEGMENT
) -> List[GenerationTask]:
    """
    Recursively scans input_dir for storyboard*.json files and creates GenerationTasks.
    Also scaffolds the standard 'asset' directory structure for each found file.
    """
    tasks = []
    
    if not input_dir.exists():
        logger.error(f"Input directory not found: {input_dir}")
        return []

    logger.info(f"Scanning for storyboard*.json files in {input_dir}")

    # Recursive scan
    for json_file in input_dir.rglob("storyboard*.json"):
        try:
            logger.debug(f"Parsing file: {json_file}")
            
            # 1. Initialize Asset Structure
            asset_mgr = AssetManager(json_file)
            asset_mgr.scaffold()
            
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validate schema
            storyboard = Storyboard(**data)
            
            # Determine output directory base for this file
            if output_mode == "in_place":
                # {Source_Dir}/{Json_Filename}_assets/{Segment}
                base_output_dir = json_file.parent / f"{json_file.stem}_assets"
            else:
                # {Output_Root}/{Relative_Path_From_Input}/{Json_Filename}/{Segment}
                # Example: input/projectA/storyboard.json -> output/projectA/storyboard/
                
                # Calculate relative path to preserve structure if using default input dir
                # If using custom absolute path, we might just use the filename or relative to the search root
                try:
                    rel_path = json_file.parent.relative_to(input_dir)
                except ValueError:
                    # Should not happen given rglob, but safe fallback
                    rel_path = Path(".")
                
                target_root = override_output_dir if override_output_dir else settings.DEFAULT_OUTPUT_DIR
                base_output_dir = target_root / rel_path / json_file.stem

            # Create tasks for each segment and version
            for segment in storyboard.segments:
                # Segment specific folder: .../{Segment_Index}/
                # Adding segment_index to path ensures grouping
                segment_dir = base_output_dir / f"Segment_{segment.segment_index}"
                
                for v in range(1, gen_count + 1):
                    task_id = f"{json_file.stem}_s{segment.segment_index}_v{v}"
                    
                    task = GenerationTask(
                        id=task_id,
                        source_file=json_file,
                        segment=segment,
                        version_index=v,
                        output_dir=segment_dir
                    )
                    tasks.append(task)
                    
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {json_file}: {e}")
        except Exception as e:
            logger.error(f"Error processing {json_file}: {e}")

    logger.info(f"Discovered {len(tasks)} tasks from {input_dir}")
    return tasks
