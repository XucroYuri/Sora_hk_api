import re
from typing import List, Optional, Literal
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.panel import Panel
from .models import GenerationTask

console = Console()

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
    Interactively asks user to supply IDs for characters found in prompts.
    """
    console.print(Panel("🕵️  角色 ID 注入检查 (Character ID Injection)", style="cyan"))
    
    all_prompts = [t.segment.prompt_text for t in tasks]
    
    console.print("此步骤用于检测 Prompt 中的中文角色名，并补充官方 Character ID。")
    if not Confirm.ask("是否进入角色 ID 修正/补充流程? [dim](可选)[/dim]"):
        return

    console.print("[dim]提示: 角色 ID (Character ID) 应与 Sora 官方创建且公开使用的 ID 保持一致。[/dim]")

    while True:
        name = Prompt.ask("请输入角色中文名称 (输入 q 结束)")
        if name.lower() == 'q':
            break
        
        count = sum(1 for p in all_prompts if name in p)
        if count == 0:
            console.print(f"[yellow]未在 Prompt 中找到角色 '{name}'[/yellow]")
            continue
            
        char_id = Prompt.ask(f"请输入 '{name}' 的角色ID [dim](需与 Sora 官方公开 ID 一致，直接回车可跳过)[/dim]", default="")
        if not char_id:
            continue
            
        formatted_id = f" (@{char_id} )" 
        
        replaced_count = 0
        for t in tasks:
            if name in t.segment.prompt_text:
                pattern = fr"{re.escape(name)}(?!\s*[（\(]@)"
                new_prompt = re.sub(pattern, f"{name}{formatted_id}", t.segment.prompt_text)
                
                if new_prompt != t.segment.prompt_text:
                    t.segment.prompt_text = new_prompt
                    replaced_count += 1
                    full_char_str = f"{name} @{char_id}"
                    if t.segment.asset and full_char_str not in t.segment.asset.characters:
                        t.segment.asset.characters.append(full_char_str)

        console.print(f"[green]已在 {replaced_count} 个 Prompt 中注入了 ID。[/green]")

    console.print("[dim]角色 ID 注入完成。[/dim]\n")
