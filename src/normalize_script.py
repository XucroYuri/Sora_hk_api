import os
import json
import re
from pathlib import Path

# Configuration
SOURCE_ROOT = Path("/Volumes/SSD/Obsidian/01-Projects/进行中")
TEMPLATE_FIELDS = {
    "image_url": None,
    "is_pro": False,
    "resolution": "horizontal",
    "duration_seconds": 10
}

def extract_json_from_md(content):
    match = re.search(r'```json\s*([\s\S]*?)\s*```', content)
    json_str = match.group(1) if match else None
    
    if not json_str:
        match = re.search(r'\{[\s\S]*\}', content)
        if match:
            json_str = match.group(0)
            
    if json_str:
        # Fix 1: Specific known issue 'in_the_style_of_"..."'
        json_str = re.sub(r'in_the_style_of_"([^"]+?)"', r"in_the_style_of_'\1'", json_str)
        # Fix 3: Remove trailing commas
        json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
        
    return json_str

def enforce_character_id_format(text):
    if not text:
        return ""
    # 1. Ensure space BEFORE @id
    text = re.sub(r'(?<!\s)(@\w+)', r' \1', text)
    # 2. Ensure space AFTER @id (Always add space)
    # Note: This is simpler and avoids regex backtracking issues with lookaheads
    text = re.sub(r'(@\w+)', r'\1 ', text)
    # 3. Collapse multiple spaces
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_asset_info(prompt_text):
    asset = {
        "characters": [],
        "scene": None,
        "props": []
    }
    if not prompt_text:
        return asset

    scene_match = re.search(r'[;；]\s*场景[：:]\s*(.*?)[;；]', prompt_text)
    if scene_match:
        asset["scene"] = scene_match.group(1).strip()

    matches = re.findall(r'([\u4e00-\u9fa5a-zA-Z0-9]+)\s+(@\w+)', prompt_text)
    for name, char_id in matches:
        clean_id = char_id.strip()
        full_char = f"{name} {clean_id}"
        if full_char not in asset["characters"]:
            asset["characters"].append(full_char)
            
    return asset

def normalize_segment(segment):
    raw_prompt = segment.get("prompt_text", "")
    clean_prompt = enforce_character_id_format(raw_prompt)
    extracted_asset = extract_asset_info(clean_prompt)
    
    existing_asset = segment.get("asset", {})
    if not existing_asset:
        existing_asset = extracted_asset
    else:
        for k in ["characters", "scene", "props"]:
            if k not in existing_asset:
                existing_asset[k] = [] if k != "scene" else None
        
        if not existing_asset.get("scene") and extracted_asset["scene"]:
            existing_asset["scene"] = extracted_asset["scene"]
        
        for c in extracted_asset["characters"]:
            if c not in existing_asset["characters"]:
                existing_asset["characters"].append(c)

    new_seg = {
        "segment_index": segment.get("segment_index"),
        "prompt_text": clean_prompt,
        "image_url": segment.get("image_url", TEMPLATE_FIELDS["image_url"]),
        "asset": existing_asset,
        "duration_seconds": segment.get("duration_seconds", TEMPLATE_FIELDS["duration_seconds"]),
        "is_pro": segment.get("is_pro", TEMPLATE_FIELDS["is_pro"]),
        "resolution": segment.get("resolution", TEMPLATE_FIELDS["resolution"]),
        "director_intent": segment.get("director_intent")
    }
    return new_seg

def process_directory_from_md(md_path: Path):
    print(f"Processing: {md_path.name}")
    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        json_str = extract_json_from_md(content)
        if not json_str:
            print(f"  [WARN] No JSON block found")
            return

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            print(f"  [DEBUG] JSON Load Failed: {e}. Attempting aggressive fix...")
            json_str_fixed = json_str.replace('in_the_style_of_"KAI XIN CHUI CHUI"', "in_the_style_of_'KAI XIN CHUI CHUI'")
            try:
                data = json.loads(json_str_fixed)
                print("  [OK] Aggressive fix worked.")
            except json.JSONDecodeError as e:
                print(f"  [ERROR] Aggressive fix failed: {e}")
                return

        if "segments" not in data:
            return

        normalized_segments = [normalize_segment(seg) for seg in data["segments"]]
        
        new_data = {
            "_comment": f"Standardized from {md_path.name}",
            "segments": normalized_segments
        }

        clean_name = md_path.stem.replace("[分镜-", "").replace("]", "")
        output_name = f"storyboard_{clean_name}.json"
        output_path = md_path.parent / output_name

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(new_data, f, indent=2, ensure_ascii=False)
            
        print(f"  [OK] Saved to: {output_path}")

    except (OSError, json.JSONDecodeError, ValueError) as e:
        print(f"  [ERROR] Failed: {e}")

def main():
    if not SOURCE_ROOT.exists():
        return
    
    print(f"Scanning {SOURCE_ROOT}...")
    for root, dirs, files in os.walk(SOURCE_ROOT):
        for file in files:
            if file.startswith("[分镜-") and file.endswith(".md"):
                process_directory_from_md(Path(root) / file)

if __name__ == "__main__":
    main()
