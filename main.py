import argparse
import sys
import signal
import logging
import json
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Third-party libraries
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn
from rich.logging import RichHandler
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

# Local modules
from src.config import settings, setup_logging
from src.scanner import discover_tasks
from src.api_client import SoraClient
from src.worker import process_task
from src.models import GenerationTask
from src.concurrency import init_controller
from src.interactor import (
    interactive_asset_injection, 
    show_task_summary, 
    interactive_resolution_override,
    interactive_image_injection,
    save_tasks_to_json,
    interactive_execution_config,
    validate_and_fix_image_urls
)

# Setup Rich Console
console = Console()
executor = None

def signal_handler(sig, frame):
    console.print("\n[bold red]正在停止... (接收到中断信号)[/bold red]")
    console.print("[yellow]请耐心等待当前正在进行的 API 请求或文件写入完成 (这是为了保护您的数据)...[/yellow]")
    raise KeyboardInterrupt

signal.signal(signal.SIGINT, signal_handler)

def run_wizard_mode(args):
    """
    交互式向导流程
    """
    # Header
    console.print(Panel.fit("[bold magenta]CineFlow (影流) - 通用视频生成流水线[/bold magenta]\n[dim]Universal Video Generation Pipeline[/dim]", border_style="magenta"))
    
    # --- Step 1: Input Source & Scan Loop ---
    tasks = []
    input_dir = None
    
    while True:
        console.print("\n[bold cyan]1. 选择输入来源 (Input Source)[/bold cyan]")
        
        # Determine default
        default_path = args.input_dir if args.input_dir else settings.DEFAULT_INPUT_DIR
        
        user_path_str = Prompt.ask(
            "请输入分镜 JSON 所在的目录路径", 
            default=str(default_path)
        )
        input_dir = Path(user_path_str)
        
        if not input_dir.exists():
            console.print(f"[red]❌ 路径不存在: {input_dir}[/red]")
            if not Confirm.ask("是否重新输入?"):
                sys.exit(0)
            continue
            
        if not input_dir.is_dir():
            console.print(f"[red]❌ 该路径不是一个目录 (请选择文件夹): {input_dir}[/red]")
            if not Confirm.ask("是否重新输入?"):
                sys.exit(0)
            continue
            
        # Scan
        with console.status(f"[bold green]正在扫描任务...[/bold green]"):
            # We assume default output mode for scanning context first
            temp_tasks = discover_tasks(input_dir, "centralized")
            
        if not temp_tasks:
            console.print(f"[yellow]⚠ 在该目录下未找到有效的 storyboard*.json 文件。[/yellow]")
            if Confirm.ask("是否尝试其他目录?"):
                continue
            else:
                sys.exit(0)
        
        # Show Summary
        show_task_summary(temp_tasks, str(input_dir))
        
        if Confirm.ask("任务列表确认无误? (Yes=下一步, No=重新选择目录)"):
            tasks = temp_tasks
            break
            
    # --- Step 2: Pre-processing (Character ID & Resolution & Image Injection) ---
    console.print("\n[bold cyan]2. 任务预处理 (Pre-process)[/bold cyan]")
    
    # 2.1 Character ID
    interactive_asset_injection(tasks)
    
    # 2.2 Resolution
    interactive_resolution_override(tasks)
    
    # 2.3 Start Frame Injection (COS Upload)
    interactive_image_injection(tasks)
    
    # 2.4 Validate Image URLs
    validate_and_fix_image_urls(tasks)
    
    # 2.5 Save Changes (Persist all pre-processing)
    save_tasks_to_json(tasks)
    
    # --- Step 3: Execution Configuration ---
    # Configure count, concurrency, filter segments
    tasks, gen_count, concurrency = interactive_execution_config(tasks)
    
    # --- Step 4: Output Configuration ---
    console.print("\n[bold cyan]4. 结果保存配置 (Output Configuration)[/bold cyan]")
    
    output_mode = args.output_mode # Default from args
    
    # If user didn't explicitly set flag, ask them
    # (Checking if args are default is tricky, simpler to just ask with default)
    console.print("请选择视频生成结果的保存方式:")
    console.print("  [1] [bold green]集中存储[/bold green] (./output/...) - 默认")
    console.print("  [2] [bold yellow]原位存储[/bold yellow] (在输入文件同级目录创建 _assets 文件夹)")
    console.print("  [3] [bold cyan]自定义路径[/bold cyan] (输入指定目录)")
    
    choice = Prompt.ask("请输入选项", choices=["1", "2", "3"], default="1")
    
    if choice == "2":
        output_mode = "in_place"
        console.print("[dim]正在更新任务输出路径...[/dim]")
        for task in tasks:
            # Re-calculate output dir for the filtered/new tasks
            base_output_dir = task.source_file.parent / f"{task.source_file.stem}_assets"
            task.output_dir = base_output_dir / f"Segment_{task.segment.segment_index}"
            
    elif choice == "3":
        output_mode = "custom"
        custom_path_str = Prompt.ask("请输入目标存储目录路径")
        custom_root = Path(custom_path_str)
        console.print(f"[dim]正在更新任务输出路径至: {custom_root}[/dim]")
        
        for task in tasks:
            # Re-calculate output dir: Custom_Root/{Json_Filename}/Segment_X
            # We maintain the project/file structure to avoid flat collisions
            base_output_dir = custom_root / task.source_file.stem
            task.output_dir = base_output_dir / f"Segment_{task.segment.segment_index}"
            
    else:
        output_mode = "centralized"
        
    console.print(f"已选择模式: [bold]{output_mode}[/bold]")

    # --- Step 5: Final Confirmation ---
    console.print("\n[bold cyan]5. 最终确认 (Final Review)[/bold cyan]")
    console.print(f"即将开始处理 [bold]{len(tasks)}[/bold] 个任务。")
    console.print(f"每分镜版本数: [bold]{gen_count}[/bold]")
    console.print(f"最大并发数: [bold]{concurrency}[/bold]")
    
    if args.dry_run:
        console.print("[bold yellow]注意: 当前为空跑模式 (Dry Run)，不会真实扣费。[/bold yellow]")
        
    if not Confirm.ask("🚀 确认开始执行生成队列?", default=True):
        console.print("[yellow]已取消操作。[/yellow]")
        sys.exit(0)

    # Return configured tasks and concurrency
    return tasks, concurrency

def main():
    parser = argparse.ArgumentParser(description="Sora 视频批量生成工具")
    parser.add_argument("--input-dir", type=Path, help="自定义输入目录")
    parser.add_argument("--output-mode", choices=["centralized", "in_place"], default="centralized")
    parser.add_argument("--dry-run", action="store_true", help="空跑模式")
    parser.add_argument("--force", action="store_true", help="强制覆盖")
    parser.add_argument("--verbose", action="store_true", help="详细日志")
    args = parser.parse_args()

    setup_logging(args.verbose)
    logging.getLogger().addHandler(RichHandler(console=console, show_path=False, markup=True))

    # Initialize Client
    try:
        client = SoraClient()
    except Exception as e:
        console.print(f"[bold red]✘ API 客户端初始化失败: {e}[/bold red]")
        sys.exit(1)

    # Run Wizard
    tasks, concurrency = run_wizard_mode(args)

    # Initialize Controller with user-selected concurrency
    init_controller(concurrency)
    
    # Execution
    console.print("\n[bold green]=== 开始执行队列 ===[/bold green]")
    
    failed_tasks = []
    skipped_count = 0
    completed_count = 0
    
    global executor
    interrupted = False
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            console=console
        ) as progress:
            
            overall_task = progress.add_task("[green]总进度", total=len(tasks))
            
            # Use the user-configured concurrency
            executor = ThreadPoolExecutor(max_workers=concurrency)
            try:
                future_to_task = {
                    executor.submit(process_task, task, client, args.dry_run, args.force): task 
                    for task in tasks
                }
                
                for future in as_completed(future_to_task):
                    task = future_to_task[future]
                    try:
                        result = future.result()
                        if result == "failed":
                            failed_tasks.append(task.id)
                            progress.console.print(f"[red]✘ 任务失败: {task.id}[/red]")
                        elif result == "skipped":
                            skipped_count += 1
                        else:
                            completed_count += 1
                            progress.console.print(f"[blue]✔ 任务完成: {task.id}[/blue]")
                    except Exception as exc:
                        failed_tasks.append(task.id)
                        console.print(f"[red]Task {task.id} 异常: {exc}[/red]")
                    
                    progress.advance(overall_task)
            except KeyboardInterrupt:
                interrupted = True
                raise
            finally:
                if executor:
                    executor.shutdown(wait=not interrupted, cancel_futures=interrupted)
                    executor = None
    
    except KeyboardInterrupt:
        console.print("\n[bold red]正在终止所有任务...[/bold red]")

    # Summary
    console.print("\n" + "="*30)
    console.print(f"[bold]执行报告[/bold]")
    console.print(f"✔ 成功: [green]{completed_count}[/green]")
    console.print(f"⏭ 跳过: [dim]{skipped_count}[/dim]")
    
    if failed_tasks:
        console.print(f"✘ 失败: [red]{len(failed_tasks)}[/red]")
        with open("failed_tasks_log.json", "w", encoding='utf-8') as f:
            json.dump(failed_tasks, f, indent=2)
        console.print(f"失败日志: failed_tasks_log.json")
    else:
        console.print("[bold green]✨ 所有任务处理完毕！[/bold green]")
        
    console.print("\n请前往输出目录验收结果。")
    console.print("="*30 + "\n")

if __name__ == "__main__":
    main()
