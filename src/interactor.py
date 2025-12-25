from typing import List, Optional, Literal, Dict, Any, Tuple
from collections import Counter
from pathlib import Path
import re
import json
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.panel import Panel
from .models import GenerationTask
from .asset_manager import AssetManager
from .storage import TencentCOSClient
from .config import settings

console = Console()

def interactive_execution_config(tasks: List[GenerationTask]) -> Tuple[List[GenerationTask], int, int]:
    """
    Step 3: Configure execution parameters before starting.
    Returns: (filtered_tasks, gen_count, concurrency)
    """
    console.print(Panel("⚙️  任务执行配置 (Task Execution Config)", style="cyan"))
    
    # 1. Generation Count per Segment
    gen_count = int(Prompt.ask(
        "每个分镜生成版本数量 (Versions per Segment)", 
        default=str(settings.GEN_COUNT_PER_SEGMENT)
    ))
    
    # 2. Concurrency
    concurrency = int(Prompt.ask(
        "最大并发任务数 (Max Concurrent Tasks)", 
        default=str(settings.MAX_CONCURRENT_TASKS)
    ))
    
    # 3. Segment Filter
    # Extract available segment indices
    all_indices = sorted(list(set(t.segment.segment_index for t in tasks)))
    min_idx, max_idx = min(all_indices), max(all_indices)
    
    console.print(f"当前任务包含分镜范围: [bold]{min_idx} - {max_idx}[/bold] (共 {len(all_indices)} 个分镜)")
    range_input = Prompt.ask(
        "请输入要生成的分镜范围 (例如 '1-5, 8, 10' 或 'all')", 
        default="all"
    )
    
    # Filter Tasks
    selected_indices = set()
    if range_input.lower() == "all":
        selected_indices = set(all_indices)
    else:
        # Parse range string
        parts = range_input.split(',')
        for part in parts:
            part = part.strip()
            if '-' in part:
                try:
                    start, end = map(int, part.split('-'))
                    selected_indices.update(range(start, end + 1))
                except ValueError:
                    console.print(f"[red]忽略无效范围格式: {part}[/red]")
            else:
                try:
                    selected_indices.add(int(part))
                except ValueError:
                    console.print(f"[red]忽略无效数字: {part}[/red]")
    
    # Filter original tasks list based on selected indices
    # AND Adjust for the new gen_count (versions)
    # We need to regenerate the tasks list because version count might change
    
    new_tasks = []
    # Group by (source_file, segment_index) to avoid duplicates if input `tasks` already has multiple versions
    # Actually, `tasks` input might already have v1, v2. We should pick unique segments and re-generate tasks.
    
    unique_segments = {} # (source_file, segment_index) -> Segment
    for t in tasks:
        key = (t.source_file, t.segment.segment_index)
        if key not in unique_segments:
            unique_segments[key] = t.segment
            
    # Re-create tasks
    for (source_file, idx), segment in unique_segments.items():
        if idx in selected_indices:
            # Create N versions
            # Output dir logic needs to be preserved or re-calculated.
            # Assuming task.output_dir logic in scanner.py: segment_dir / ...
            # We can re-use the logic or just grab it from one of the existing tasks
            
            # Simple way: find a prototype task for this segment to get output_dir base
            # But output_dir in GenerationTask includes version? No, usually task.output_dir is segment dir?
            # Let's check models.py or scanner.py
            # scanner.py: task.output_dir = segment_dir
            # models.py: output_filename_base uses version_index
            
            # We need to reconstruct the path. 
            # scanner.py logic:
            # if output_mode == "in_place": base = ...
            # else: base = ...
            
            # To avoid duplicating logic, we can try to find an existing task for this segment and copy its output_dir
            prototype_task = next((t for t in tasks if t.source_file == source_file and t.segment.segment_index == idx), None)
            
            if prototype_task:
                base_dir = prototype_task.output_dir
                for v in range(1, gen_count + 1):
                     new_task = GenerationTask(
                        id=f"{source_file.stem}_s{idx}_v{v}",
                        source_file=source_file,
                        segment=segment,
                        version_index=v,
                        output_dir=base_dir
                    )
                     new_tasks.append(new_task)

    console.print(f"[green]已配置任务队列:[/green] {len(new_tasks)} 个任务 (分镜数: {len(selected_indices)}, 每分镜 {gen_count} 版本)")
    
    return new_tasks, gen_count, concurrency

def validate_and_fix_image_urls(tasks: List[GenerationTask]):
    """
    Validates image_url in tasks.
    1. Checks for HTTP/HTTPS prefix.
    2. Strips whitespace.
    3. Nullifies invalid URLs.
    """
    console.print(Panel("🔍  图片链接校验 (Image URL Validation)", style="cyan"))
    
    fixed_count = 0
    invalid_count = 0
    
    # Iterate unique segments to avoid double counting/fixing
    seen_segments = set()
    
    for t in tasks:
        seg = t.segment
        if id(seg) in seen_segments:
            continue
        seen_segments.add(id(seg))
        
        url = seg.image_url
        if url:
            original_url = url
            # 1. Strip whitespace
            url = url.strip()
            
            # 2. Check Valid URL
            if not url.startswith(("http://", "https://")):
                console.print(f"[yellow]⚠ Segment {seg.segment_index}: 无效 URL (非 http/https)，已移除[/yellow]: {url}")
                seg.image_url = None
                invalid_count += 1
                continue
                
            # 3. Check for specific bad patterns (e.g. trailing parenthesis from markdown)
            # This handles the case where user manually entered a bad URL in JSON
            if url.endswith(')'):
                console.print(f"[yellow]⚠ Segment {seg.segment_index}: 发现末尾多余括号，尝试修复[/yellow]: {url}")
                url = url.rstrip(')')
                
            if url != original_url:
                seg.image_url = url
                fixed_count += 1
                
    if fixed_count > 0 or invalid_count > 0:
        console.print(f"[green]校验完成: 修复 {fixed_count} 个链接, 移除 {invalid_count} 个无效链接。[/green]")
        # We should save these fixes back to JSON
        try:
            save_tasks_to_json(tasks)
        except:
            pass
    else:
        console.print("[dim]所有图片链接格式正常。[/dim]")

def show_task_summary(tasks: List[GenerationTask], input_dir: str):
    """
    显示任务扫描结果摘要表格
    """
    unique_files = len(set(t.source_file for t in tasks))
    total_segments = len(set(f"{t.source_file}_{t.segment.segment_index}" for t in tasks))
    total_duration = sum(t.segment.duration_seconds for t in tasks)
    estimated_cost = total_duration * 0.005
    
    # Count resolutions
    res_stats = {"horizontal": 0, "vertical": 0}
    for t in tasks:
        res_stats[t.segment.resolution] += 1
    res_str = f"H:{res_stats['horizontal']} / V:{res_stats['vertical']}"
    
    table = Table(title="任务扫描概览 (Scan Summary)", show_header=True, header_style="bold magenta")
    table.add_column("项目 (Item)", style="cyan")
    table.add_column("数值 (Value)", style="green")
    
    table.add_row("输入目录 (Source)", str(input_dir))
    table.add_row("文件数量 (Files)", str(unique_files))
    table.add_row("分镜总数 (Segments)", str(total_segments))
    table.add_row("生成任务 (Total Tasks)", f"{len(tasks)} (含重复变体)")
    table.add_row("分辨率分布 (Resolution)", res_str)
    table.add_row("预计总时长 (Duration)", f"{total_duration} 秒")
    table.add_row("预估成本 (Est. Cost)", f"${estimated_cost:.2f}")
    
    console.print(table)

def interactive_resolution_override(tasks: List[GenerationTask]):
    """
    允许用户强制覆盖所有任务的分辨率
    """
    console.print(Panel("📺 分辨率检查 (Resolution Check)", style="cyan"))
    
    # Check if mixed
    res_types = set(t.segment.resolution for t in tasks)
    is_mixed = len(res_types) > 1
    
    if is_mixed:
        console.print("[yellow]⚠ 检测到任务列表中包含混合分辨率 (横屏/竖屏)。[/yellow]")
    else:
        current = list(res_types)[0]
        console.print(f"当前所有任务分辨率统一为: [bold green]{current}[/bold green]")
        
    console.print("您希望统一修改本批次的分辨率吗?")
    console.print("  [0] 保持原样 (Keep Original)")
    console.print("  [1] 统一为横屏 (Horizontal 16:9)")
    console.print("  [2] 统一为竖屏 (Vertical 9:16)")
    
    choice = Prompt.ask("请选择", choices=["0", "1", "2"], default="0")
    
    if choice == "0":
        return
        
    target_res: Literal["horizontal", "vertical"] = "horizontal" if choice == "1" else "vertical"
    
    count = 0
    for t in tasks:
        if t.segment.resolution != target_res:
            t.segment.resolution = target_res
            count += 1
            
    if count > 0:
        console.print(f"[green]已将 {count} 个任务的分辨率更新为 {target_res}。[/green]")
    else:
        console.print("[dim]无需更新，所有任务已匹配目标分辨率。[/dim]")

def interactive_asset_injection(tasks: List[GenerationTask]):
    """
    Interactive workflow to inject Character IDs.
    Scans ONLY explicit names defined in JSON asset.characters.
    Handles existing IDs by allowing overwrite or skip.
    """
    console.print(Panel("🕵️  角色 ID 注入检查 (Character ID Injection)", style="cyan"))
    
    console.print("此步骤将扫描 JSON 中已定义的角色名称，并辅助您补充或修正官方 ID。")
    if not Confirm.ask("是否开始扫描并修正?", default=True):
        return

    # --- Phase 1: Scan & Analyze ---
    with console.status("[bold green]正在分析 JSON 资产...[/bold green]"):
        file_char_map = {}  # {file_name: Counter(char_name: count)}
        global_char_stats = {} # {char_name: {'files': set(), 'count': 0, 'existing_ids': set()}}

        for task in tasks:
            f_name = task.source_file.name
            if f_name not in file_char_map:
                file_char_map[f_name] = Counter()
            
            for char_str in task.segment.asset.characters:
                # Robust parsing of "Name", "Name@ID", "Name (@ID )"
                name, found_id = _parse_name_and_id(char_str)
                
                if name:
                    file_char_map[f_name][name] += 1
                    
                    if name not in global_char_stats:
                        global_char_stats[name] = {'files': set(), 'count': 0, 'existing_ids': set()}
                    
                    global_char_stats[name]['files'].add(f_name)
                    global_char_stats[name]['count'] += 1
                    if found_id:
                        global_char_stats[name]['existing_ids'].add(found_id)

    if not global_char_stats:
        console.print("[yellow]未在 JSON 文件的 Asset -> Characters 中找到任何角色定义。[/yellow]")
        return

    # --- Phase 2: Report ---
    console.print("\n[bold]📄 待处理角色列表 (Characters from JSON):[/bold]")
    for f_name, counter in file_char_map.items():
        if not counter:
            continue
        chars_list = [f"{k}" for k, v in counter.items()]
        console.print(f" • [cyan]{f_name}[/cyan]: {', '.join(chars_list)}")

    # --- Phase 3: Interactive Injection ---
    sorted_candidates = sorted(global_char_stats.items(), key=lambda x: x[1]['count'], reverse=True)
    
    console.print("\n[bold]🚀 开始 ID 补充流程[/bold]")
    console.print("操作指南: 输入新 ID 回车覆盖。直接 [bold]回车[/bold] 则保持当前状态(跳过)。输入 'q' 结束。")
    console.print("         输入 [bold red]rm[/bold red] (或 clear, del) 可清除当前角色的 ID 绑定。")
    
    for name, stats in sorted_candidates:
        existing_ids = stats['existing_ids']
        existing_str = ", ".join(existing_ids) if existing_ids else "[dim]无[/dim]"
        status_color = "green" if existing_ids else "yellow"
        
        console.print(f"\n角色名称: [bold white]{name}[/bold white] (涉及 {stats['count']} 个分镜)")
        console.print(f"[dim]所在文件: {', '.join(list(stats['files'])[:3])}{'...' if len(stats['files'])>3 else ''}[/dim]")
        console.print(f"当前 ID: [{status_color}]{existing_str}[/{status_color}]")
        
        prompt_text = f"请输入 '{name}' 的新 ID" if existing_ids else f"请输入 '{name}' 的 ID"
        char_id = Prompt.ask(prompt_text, default="")
        
        if char_id.lower() == 'q':
            break
        
        if char_id.lower() in ['rm', 'clear', 'del']:
            _remove_id_injection(tasks, name)
            continue
            
        if char_id.strip():
            # User provided an ID, apply injection/replacement
            clean_id = char_id.strip()
            _apply_id_injection(tasks, name, clean_id)
        else:
            console.print("[dim]⏭ 保持原状 (跳过)[/dim]")

    console.print("[dim]角色 ID 注入完成。[/dim]\n")

def _remove_id_injection(tasks: List[GenerationTask], name: str):
    """
    Helper to remove ID injection.
    1. Reverts Prompt to: Name
    2. Reverts Asset to: Name
    """
    replaced_count = 0
    
    for t in tasks:
        # 1. Update Prompt Text
        # Find "Name (@ID )" or "Name (@ID)"
        # Regex: Name followed by optional existing tag (\s*\(@[^)]+\))
        # We replace the whole match with just "Name"
        pattern = fr"{re.escape(name)}\s*\(@[^)]+\)"
        if re.search(pattern, t.segment.prompt_text):
            new_prompt = re.sub(pattern, name, t.segment.prompt_text)
            if new_prompt != t.segment.prompt_text:
                t.segment.prompt_text = new_prompt
                replaced_count += 1
                
        # 2. Update Asset metadata
        new_char_list = []
        updated_asset = False
        for c in t.segment.asset.characters:
            c_name, _ = _parse_name_and_id(c)
            if c_name == name:
                # If currently has ID (e.g. Name@ID), revert to Name
                if c != name:
                    new_char_list.append(name)
                    updated_asset = True
                else:
                    new_char_list.append(c)
            else:
                new_char_list.append(c)
        
        if updated_asset:
            t.segment.asset.characters = new_char_list

    if replaced_count > 0 or updated_asset:
        console.print(f" -> [yellow]已移除 {name} 的 ID 绑定 ({replaced_count} 处 Prompt 更新)。[/yellow]")
    else:
        console.print(f" -> [dim]未发现需要移除的 ID 绑定。[/dim]")

def interactive_image_injection(tasks: List[GenerationTask]):
    """
    Scans for local start frame images in asset/segment/, uploads them to COS, 
    and updates the JSON image_url field.
    """
    console.print(Panel("🖼️  参考图注入检查 (Start Frame Injection)", style="cyan"))
    
    # Check if COS is configured
    try:
        cos_client = TencentCOSClient()
        if not cos_client.enabled:
            console.print("[yellow]未检测到腾讯云 COS 配置，跳过图片上传步骤。[/yellow]")
            return
    except Exception as e:
        console.print(f"[red]COS 客户端初始化失败: {e}[/red]")
        return

    console.print("此步骤将扫描 'asset/segment/' 目录下的起始帧图片，并上传至对象存储。")
    if not Confirm.ask("是否开始扫描并上传?", default=True):
        return

    # 1. Identify unique segments
    # Use a dict to map (source_file, segment_index) -> task (representative)
    unique_segments = {}
    for t in tasks:
        key = (t.source_file, t.segment.segment_index)
        if key not in unique_segments:
            unique_segments[key] = t

    processed_count = 0
    uploaded_count = 0
    
    for (source_file, seg_idx), task in unique_segments.items():
        asset_mgr = AssetManager(source_file)
        
        # Look for start image (e.g., 1_start.png)
        start_img_path = asset_mgr.get_segment_image(seg_idx, "start")
        
        if start_img_path:
            console.print(f"\n[cyan]发现本地图片[/cyan]: {start_img_path.name} (Segment {seg_idx})")
            
            # Check existing URL
            existing_url = task.segment.image_url
            should_upload = True
            
            if existing_url:
                console.print(f"  [dim]当前 image_url: {existing_url}[/dim]")
                # If it looks like a COS URL we just uploaded, maybe skip?
                # For now, simplistic check: prompt user
                should_upload = Confirm.ask(f"  Segment {seg_idx} 已存在链接，是否上传本地图片并覆盖?", default=False)
            
            if should_upload:
                # Upload
                with console.status(f"[green]正在上传 {start_img_path.name}...[/green]"):
                    url = cos_client.upload_file(start_img_path)
                    
                if url:
                    # Update all tasks sharing this segment
                    task.segment.image_url = url
                    uploaded_count += 1
                    
                    # IMMEDIATE PERSISTENCE
                    # Save this change to the JSON file right now
                    try:
                        _persist_segment_change(task.source_file, task.segment)
                        console.print(f"  [green]✔ 上传并保存成功:[/green] {url}")
                    except Exception as e:
                        console.print(f"  [red]⚠ 上传成功但保存JSON失败: {e}[/red]")
                else:
                    console.print(f"  [red]✘ 上传失败[/red]")
            else:
                console.print("  [dim]⏭ 跳过[/dim]")
                
            processed_count += 1

    console.print(f"\n[bold]处理完成[/bold]: 扫描 {processed_count} 个本地资产，上传更新 {uploaded_count} 个。")
    console.print("[dim]注意: 所有更改已实时写入 JSON 文件。[/dim]\n")

def _persist_segment_change(source_file: Path, segment: Any):
    """
    Helper to save a single segment's changes to its source JSON file immediately.
    """
    with open(source_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    changed = False
    for seg_dict in data.get("segments", []):
        if seg_dict.get("segment_index") == segment.segment_index:
            # Check and update fields
            # We focus on image_url here, but might as well sync others if we have the object
            if seg_dict.get("image_url") != segment.image_url:
                seg_dict["image_url"] = segment.image_url
                changed = True
            
            # Sync other potential changes (just in case)
            if seg_dict.get("prompt_text") != segment.prompt_text:
                seg_dict["prompt_text"] = segment.prompt_text
                changed = True
                
            if seg_dict.get("asset") != segment.asset.model_dump():
                seg_dict["asset"] = segment.asset.model_dump()
                changed = True
                
            if seg_dict.get("resolution") != segment.resolution:
                seg_dict["resolution"] = segment.resolution
                changed = True
            break
            
    if changed:
        with open(source_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

def save_tasks_to_json(tasks: List[GenerationTask]):
    """
    Persists changes (Prompt, Asset, Image URL) back to the source JSON files.
    """
    console.print(Panel("💾 保存更改 (Save Changes)", style="cyan"))
    
    # Group by file
    files_map = {}
    for t in tasks:
        if t.source_file not in files_map:
            files_map[t.source_file] = []
        files_map[t.source_file].append(t)
        
    updated_files = 0
    
    with console.status("[bold green]正在写入 JSON 文件...[/bold green]"):
        for source_file, task_list in files_map.items():
            try:
                # Read original to preserve _comment and structure
                with open(source_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Update segments
                # We need to map task data back to data['segments']
                # Create a map of segment_index -> Segment Object (from tasks)
                # Since all tasks for segment X share the same updated Segment object
                seg_map = {t.segment.segment_index: t.segment for t in task_list}
                
                changed = False
                for seg_dict in data.get("segments", []):
                    idx = seg_dict.get("segment_index")
                    if idx in seg_map:
                        updated_seg_obj = seg_map[idx]
                        
                        # Check specific fields we modify: prompt_text, asset, image_url, resolution
                        
                        # 1. Prompt
                        if seg_dict.get("prompt_text") != updated_seg_obj.prompt_text:
                            seg_dict["prompt_text"] = updated_seg_obj.prompt_text
                            changed = True
                            
                        # 2. Asset
                        # Convert pydantic model back to dict
                        new_asset = updated_seg_obj.asset.model_dump()
                        if seg_dict.get("asset") != new_asset:
                            seg_dict["asset"] = new_asset
                            changed = True
                            
                        # 3. Image URL
                        if seg_dict.get("image_url") != updated_seg_obj.image_url:
                            seg_dict["image_url"] = updated_seg_obj.image_url
                            changed = True

                        # 4. Resolution
                        if seg_dict.get("resolution") != updated_seg_obj.resolution:
                            seg_dict["resolution"] = updated_seg_obj.resolution
                            changed = True

                if changed:
                    with open(source_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    updated_files += 1
                    
            except Exception as e:
                console.print(f"[red]保存失败 {source_file.name}: {e}[/red]")

    if updated_files > 0:
        console.print(f"[green]已更新 {updated_files} 个 JSON 文件。[/green]\n")
    else:
        console.print("[dim]没有文件需要更新。[/dim]\n")

def _parse_name_and_id(char_str: str):
    """
    Extracts name and ID from various formats:
    - "Alice" -> ("Alice", None)
    - "Alice@123" -> ("Alice", "123")
    - "Alice (@123 )" -> ("Alice", "123")
    """
    if '@' not in char_str:
        return char_str.strip(), None
    
    # Split by first @
    # But wait, "Name (@ID)" split '@' gives "Name (" and "ID)"
    # "Name@ID" split '@' gives "Name" and "ID"
    
    # Try regex for the cleaner "Name (@ID)" pattern first
    match_paren = re.search(r'^(.*?)\s*\(@([^)]+)\)\s*$', char_str)
    if match_paren:
        name = match_paren.group(1).strip()
        raw_id = match_paren.group(2).strip()
        # raw_id might be "123 " or "123"
        return name, raw_id
    
    # Fallback to simple split for "Name@ID"
    parts = char_str.split('@')
    name = parts[0].strip()
    raw_id = parts[1].strip()
    return name, raw_id

def _apply_id_injection(tasks: List[GenerationTask], name: str, char_id: str):
    """
    Helper to apply ID injection. 
    1. Updates Prompt to: Name (@ID )
    2. Updates Asset to: Name@ID (Standardized)
    """
    # Prompt format: Name (@ID ) with trailing space for safety
    prompt_id_suffix = f" (@{char_id} )"
    # Asset format: Name@ID (also adding space just in case, per user request for general foolproofing)
    asset_id_str = f"{name}@{char_id} " 
    
    replaced_count = 0
    
    for t in tasks:
        # 1. Update Prompt Text
        if name in t.segment.prompt_text:
            # We need to replace any existing ID format for this name
            # Pattern: Name followed optionally by (@...) or nothing
            # Actually, standard replacement:
            # Find "Name" that is NOT part of an existing correct tag? 
            # Or just replace occurrences.
            
            # Simple approach: Replace "Name" + any old tag -> "Name" + new tag
            # Old tag patterns: " (@old )", "(@old)", etc.
            
            # Regex to find: Name followed by optional existing tag
            # existing tag = \s*\(@[^)]+\)
            pattern = fr"{re.escape(name)}(\s*\(@[^)]+\))?"
            
            # Replacement
            new_prompt = re.sub(pattern, f"{name}{prompt_id_suffix}", t.segment.prompt_text)
            
            if new_prompt != t.segment.prompt_text:
                t.segment.prompt_text = new_prompt
                replaced_count += 1
                
        # 2. Update Asset metadata
        # We need to find the entry for 'name' in the list and update it
        new_char_list = []
        updated_asset = False
        for c in t.segment.asset.characters:
            c_name, _ = _parse_name_and_id(c)
            if c_name == name:
                new_char_list.append(asset_id_str)
                updated_asset = True
            else:
                new_char_list.append(c)
        
        if updated_asset:
            t.segment.asset.characters = new_char_list

    if replaced_count > 0:
        console.print(f" -> [green]已更新 {replaced_count} 处 Prompt (ID: {char_id})。[/green]")
    else:
        # If we didn't update prompt (maybe name not in text), but we updated asset list
        console.print(f" -> [green]已更新关联资产定义 (ID: {char_id}) 。[/green]")
