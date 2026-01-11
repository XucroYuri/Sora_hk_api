import os
import json
import re
from pathlib import Path
from typing import List, Dict, Optional

# Configuration
SOURCE_ROOT = Path("/Volumes/SSD/Obsidian/01-Projects/进行中")

def extract_standard_roles(md_path: Path) -> List[str]:
    """
    Extracts standard character names.
    Strategy 1: Look for '角色：...' line.
    Strategy 2: Look for '**Name**' lines which indicate dialogue speakers.
    """
    roles = set()
    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        # Strategy 1: Explicit Definition
        for line in lines:
            if re.match(r'^[*【]*角色[*】]*[:：]', line):
                content = re.sub(r'^[*【]*角色[*】]*[:：]\s*', '', line).strip()
                raw_roles = re.split(r'[，,、\s]+', content)
                for r in raw_roles:
                    clean_r = re.sub(r'（.*?）|\(.*?\)', '', r).strip()
                    if clean_r:
                        roles.add(clean_r)
                break
        
        # Strategy 2: Dialogue Headers (if Strategy 1 failed or supplementary)
        if not roles:
            for line in lines:
                # Match **Name** on its own line
                m = re.match(r'^\s*\*\*([\u4e00-\u9fa5]{2,5})\*\*\s*$', line)
                if m:
                    roles.add(m.group(1))
                    
    except (OSError, UnicodeDecodeError) as e:
        print(f"[WARN] Failed to read roles from {md_path.name}: {e}")
        
    return list(roles)

def build_id_map(json_data: dict, standard_roles: List[str]) -> Dict[str, str]:
    """
    Scans the JSON to find existing Character IDs and maps them to Standard Names.
    """
    id_map = {} 
    
    # 1. Collect all name-id pairs found in the current JSON
    found_pairs = []
    for seg in json_data.get("segments", []):
        prompt = seg.get("prompt_text", "")
        # Find "Name @id" or "Name@id"
        matches = re.findall(r'([\u4e00-\u9fa5a-zA-Z0-9]+)\s*@([a-zA-Z0-9_]+)', prompt)
        found_pairs.extend(matches)
        
        # Also check asset list
        for char_str in seg.get("asset", {}).get("characters", []):
             # Remove existing backticks if any for clean matching
             clean_str = char_str.replace('`', '')
             m = re.match(r'^(.*?)\s*@([a-zA-Z0-9_]+)', clean_str)
             if m:
                 found_pairs.append(m.groups())

    # 2. Match found pairs to Standard Roles
    for found_name, found_id in found_pairs:
        found_id = found_id.strip()
        found_name = found_name.strip()
        matched_std_role = None
        
        if standard_roles:
            # Try to match against standard roles
            if found_name in standard_roles:
                matched_std_role = found_name
            else:
                # Partial match
                for std in standard_roles:
                    if found_name in std:
                        matched_std_role = std
                        break
        else:
            # If no standard roles found in MD, accept the JSON's name as truth
            matched_std_role = found_name
        
        if matched_std_role:
            # Conflict resolution: if ID exists, don't overwrite? Or overwrite?
            # Assuming consistent ID usage in JSON.
            id_map[matched_std_role] = found_id
            
    return id_map

def fix_prompt_structure(prompt: str, id_map: Dict[str, str]) -> str:
    """
    Enforces `镜头A：` and wraps roles.
    """
    # 0. Pre-clean: Remove existing backticks to allow clean re-tagging
    prompt = prompt.replace('`', '')

    # 1. Fix Shot Labels
    # Match "镜头" + any colons + space + Letter + any colons
    prompt = re.sub(r'镜头[：:]*\s*([A-Z])[：:]*', r'镜头\1：', prompt)
    
    # 2. Apply Character Standardization
    # We need to iterate carefully.
    
    # Pre-clean: Remove existing backticks to start fresh?
    # prompt = prompt.replace('`', '') 
    # Actually safer to keep them if they are correct, but standardizing is better.
    
    for role_name, role_id in id_map.items():
        # Target: Name followed by @role_id
        # We construct the strict format: `Name@ID `
        
        # Regex: Find Name (or known aliases/substrings?) + @ + ID
        # Here we only know the Standard Name -> ID mapping.
        # But in the text, it might be "ShortName @id".
        # We need to find where @id is, and capture the word before it.
        
        # Find any word before @role_id
        pattern = re.compile(rf'([\u4e00-\u9fa5a-zA-Z0-9]+)\s*@\s*{re.escape(role_id)}', re.IGNORECASE)
        
        def repl(m):
            # Replace found name with Standard Role Name
            # Add backticks and trailing space
            return f"`{role_name}@{role_id} `"
            
        prompt = pattern.sub(repl, prompt)
        
    # Remove double spaces
    prompt = re.sub(r' +', ' ', prompt)
    # Ensure space after `
    prompt = re.sub(r'`(?!\s)', '` ', prompt)
    
    return prompt.strip()

def standardize_segment(segment, id_map):
    raw_prompt = segment.get("prompt_text", "")
    new_prompt = fix_prompt_structure(raw_prompt, id_map)
    
    # Asset Cleanup
    new_chars = []
    matches = re.findall(r'`([^`]+)`', new_prompt)
    for m in matches:
        if '@' in m:
            if m not in new_chars:
                new_chars.append(m.strip())
    
    segment["prompt_text"] = new_prompt
    if "asset" not in segment:
        segment["asset"] = {}
    segment["asset"]["characters"] = new_chars
    
    return segment

def process_directory(dir_path: Path):
    md_files = list(dir_path.glob("*.md"))
    source_md = None
    for f in md_files:
        if not f.name.startswith("[分镜-") and not f.name.startswith("分镜脚本"):
            source_md = f
            break
            
    if not source_md:
        print(f"[SKIP] No source script found in {dir_path}")
        return

    standard_roles = extract_standard_roles(source_md)
    # print(f"[{dir_path.name}] Standard Roles: {standard_roles}")

    json_files = list(dir_path.glob("storyboard_*.json"))
    for json_file in json_files:
        print(f"  Processing {json_file.name}...")
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            id_map = build_id_map(data, standard_roles)
            if not id_map:
                print(f"    [WARN] No Character IDs found in JSON.")
            
            new_segments = [standardize_segment(seg, id_map) for seg in data["segments"]]
            data["segments"] = new_segments
            data["_comment"] = (data.get("_comment", "") + " | Standardized via Agent v2").strip(" |")
            
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            print(f"    [OK] Standardized.")
            
        except (OSError, json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"    [ERROR] {e}")

def main():
    if not SOURCE_ROOT.exists():
        return
    for item in SOURCE_ROOT.iterdir():
        if item.is_dir():
            process_directory(item)

if __name__ == "__main__":
    main()
