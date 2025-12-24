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

# Local modules
from src.config import settings, setup_logging
from src.scanner import discover_tasks
from src.api_client import SoraClient
from src.worker import process_task
from src.models import GenerationTask
from src.concurrency import init_controller
from src.interactor import interactive_asset_injection

# Setup Rich Console
console = Console()

# Global Executor for clean shutdown
executor = None

def signal_handler(sig, frame):
    """
    优雅退出处理器
    """
    console.print("\n[bold red]正在停止... (接收到中断信号)[/bold red]")
    console.print("[yellow]请耐心等待当前正在进行的 API 请求或文件写入完成 (这是为了保护您的数据)...[/yellow]")
    # We allow the main loop to catch KeyboardInterrupt to handle shutdown
    raise KeyboardInterrupt

signal.signal(signal.SIGINT, signal_handler)

def main():
    global executor
    parser = argparse.ArgumentParser(description="Sora 视频批量生成工具 (Sora Batch Generator)")
    
    # Argument definitions with Chinese help text
    parser.add_argument("--input-dir", type=Path, help="自定义输入目录 (默认: ./input)")
    parser.add_argument("--output-mode", choices=["centralized", "in_place"], default="centralized", 
                        help="输出模式: centralized(集中到output目录) / in_place(原位保存到JSON同级)")
    parser.add_argument("--dry-run", action="store_true", help="空跑模式: 仅估算消耗，不真实调用API")
    parser.add_argument("--force", action="store_true", help="强制覆盖: 忽略已存在的文件，重新生成")
    parser.add_argument("--verbose", action="store_true", help="详细日志: 显示更多调试信息")

    args = parser.parse_args()

    # 1. Setup Logging
    setup_logging(args.verbose)
    logging.getLogger().addHandler(RichHandler(console=console, show_path=False, markup=True))

    # Header
    console.print(Panel.fit("[bold magenta]Sora HK 批量生成工具[/bold magenta]\n[dim]Sora Batch Video Generator[/dim]", border_style="magenta"))

    # 2. Initialize Client
    try:
        client = SoraClient()
    except Exception as e:
        console.print(f"[bold red]✘ API 客户端初始化失败: {e}[/bold red]")
        sys.exit(1)

    # 3. Discovery
    input_dir = args.input_dir if args.input_dir else settings.DEFAULT_INPUT_DIR
    
    with console.status(f"[bold green]正在扫描任务...[/bold green] (路径: {input_dir})"):
        tasks = discover_tasks(input_dir, args.output_mode)
    
    if not tasks:
        console.print(f"[yellow]⚠ 在目录 '{input_dir}' 下未找到有效的 storyboard*.json 任务文件。[/yellow]")
        console.print("  [dim]提示: 请确保文件名包含 'storyboard' 且格式正确。[/dim]")
        sys.exit(0)

    # 4. Dry Run
    if args.dry_run:
        console.print(Panel(f"[bold cyan]空跑模式 (Dry Run)[/bold cyan]", expand=False))
        console.print(f"检测到任务数: [bold]{len(tasks)}[/bold]")
        
        total_seconds = sum(t.segment.duration_seconds for t in tasks)
        estimated_cost = total_seconds * 0.005 
        
        console.print(f"总视频时长: [bold]{total_seconds} 秒[/bold]")
        console.print(f"预计消耗 (估算): [bold]${estimated_cost:.2f}[/bold] (仅供参考)")
        console.print("\n[dim]示例输出路径:[/dim]")
        for t in tasks[:3]:
            console.print(f" - {t.output_dir.relative_to(settings.PROJECT_ROOT) if t.output_dir.is_relative_to(settings.PROJECT_ROOT) else t.output_dir}")
        if len(tasks) > 3:
            console.print("   ...")
        sys.exit(0)

    # 4.5 Interactive Asset Injection
    if not args.dry_run:
        # Only ask in real run (or dry run too? maybe useful to see effect)
        # User requirement: "终端交互时询问"
        interactive_asset_injection(tasks)

    # 5. Execution
    console.print(f"\n[bold]开始执行[/bold] - 任务总数: [cyan]{len(tasks)}[/cyan] | 最大并发: [cyan]{settings.MAX_CONCURRENT_TASKS}[/cyan]")
    
    # Initialize Adaptive Concurrency Controller
    init_controller(settings.MAX_CONCURRENT_TASKS)
    
    failed_tasks = []
    skipped_count = 0
    completed_count = 0
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            console=console
        ) as progress:
            
            overall_task = progress.add_task("[green]总进度 (Total)", total=len(tasks))
            
            executor = ThreadPoolExecutor(max_workers=settings.MAX_CONCURRENT_TASKS)
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
                        # Skip 不刷屏，保持界面清爽
                    else:
                        completed_count += 1
                        progress.console.print(f"[blue]✔ 任务完成: {task.id}[/blue]")
                        
                except Exception as exc:
                    failed_tasks.append(task.id)
                    console.print(f"[red]Task {task.id} 异常: {exc}[/red]")
                
                progress.advance(overall_task)
    
    except KeyboardInterrupt:
        console.print("\n[bold red]正在终止所有任务...[/bold red]")
        # Executor will exit context and wait for running threads
        if executor:
            executor.shutdown(wait=False, cancel_futures=True)

    # 6. Summary
    console.print("\n" + "="*30)
    console.print(f"[bold]执行报告[/bold]")
    console.print(f"✔ 成功: [green]{completed_count}[/green]")
    console.print(f"⏭ 跳过: [dim]{skipped_count}[/dim] (文件已存在)")
    
    if failed_tasks:
        console.print(f"✘ 失败: [red]{len(failed_tasks)}[/red]")
        log_file = "failed_tasks_log.json"
        with open(log_file, "w", encoding='utf-8') as f:
            json.dump(failed_tasks, f, indent=2)
        console.print(f"失败任务ID已保存至: [bold]{log_file}[/bold]")
    else:
        console.print("[bold green]所有任务处理完毕！[/bold green]")
    console.print("="*30 + "\n")

if __name__ == "__main__":
    main()
