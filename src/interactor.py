import re
from typing import List
from rich.console import Console
from rich.prompt import Prompt, Confirm
from .models import GenerationTask

console = Console()

def extract_potential_names(text: str) -> List[str]:
    """
    Heuristic extraction of potential Chinese names from prompt.
    Looking for patterns like "A特写王大力" or "小品挥舞".
    This is naive and relies on user interaction to confirm.
    """
    # Simple regex to find 2-3 character Chinese words that might be names
    # Only if they are NOT followed by an @id
    # Logic: Find Chinese chars, check if next non-space char is '@'
    
    # Actually, simpler approach: Ask user for names present in the batch.
    return []

def interactive_asset_injection(tasks: List[GenerationTask]):
    """
    Interactively asks user to supply IDs for characters found in prompts.
    """
    console.print("\n[bold cyan]🕵️  角色 ID 注入检查 (Character ID Injection)[/bold cyan]")
    
    # 1. Collect all prompts
    all_prompts = [t.segment.prompt_text for t in tasks]
    combined_text = " ".join(all_prompts)
    
    # 2. Check if there are characters without IDs
    # We look for user-provided names. 
    # Since we can't NLP easily, we ask user: "Any characters need IDs?"
    
    if not Confirm.ask("是否需要为本批次任务中的角色补充 ID (e.g. 小美 -> @xiaomei)? [dim](可选)[/dim]"):
        return

    console.print("[dim]提示: 角色 ID (Character ID) 应与 Sora 官方创建且公开使用的 ID 保持一致，以确保形象统一。[/dim]")

    while True:
        name = Prompt.ask("请输入角色中文名称 (输入 q 结束)")
        if name.lower() == 'q':
            break
        
        # Check if name exists in prompts
        count = sum(1 for p in all_prompts if name in p)
        if count == 0:
            console.print(f"[yellow]未在 Prompt 中找到角色 '{name}'[/yellow]")
            continue
            
        char_id = Prompt.ask(f"请输入 '{name}' 的角色ID [dim](需与 Sora 官方公开 ID 一致，直接回车可跳过该角色)[/dim]", default="")
        if not char_id:
            continue
            
        # Format: "Name (@id )"
        formatted_id = f" (@{char_id} )" # Note the space
        
        # Apply replacement
        replaced_count = 0
        for t in tasks:
            if name in t.segment.prompt_text:
                # Avoid double tagging if already exists
                # Regex lookahead to see if @char_id is already there?
                # Simple check: if "Name (@id" not in text
                
                pattern = f"{name}(?!\s*\(@{char_id})") # Negative lookahead
                
                # We replace simple occurences of Name with Name (@id )
                # But careful not to break existing tags.
                # Safer: specific user instruction was "如果Prompt中存在角色'小美'，则补充...改为'小美（@xiaomei ）'"
                
                # Replace logic:
                # Find "Name" not followed by " (@"
                
                new_prompt = re.sub(f"{name}(?!\s*[（\(]@)", f"{name}{formatted_id}", t.segment.prompt_text)
                
                if new_prompt != t.segment.prompt_text:
                    t.segment.prompt_text = new_prompt
                    replaced_count += 1
                    # Also update asset list
                    full_char_str = f"{name} @{char_id}"
                    if t.segment.asset and full_char_str not in t.segment.asset.characters:
                        t.segment.asset.characters.append(full_char_str)

        console.print(f"[green]已更新 {replaced_count} 个 Prompt 片段。[/green]")

    console.print("[dim]角色 ID 注入完成。[/dim]\n")
