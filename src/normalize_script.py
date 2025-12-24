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
        # Fix unescaped quotes in style tags
        json_str = re.sub(r'in_the_style_of_"([^"]+)"', r"in_the_style_of_'\1'", json_str)
    
    return json_str

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

    char_matches = re.findall(r'([\u4e00-\u9fa5]+)\s*(@[a-zA-Z0-9_]+)', prompt_text)
    for name, char_id in char_matches:
        full_char = f"{name} {char_id}"
        if full_char not in asset["characters"]:
            asset["characters"].append(full_char)
            
    return asset

def normalize_segment(segment):
    prompt = segment.get("prompt_text", "")
    extracted_asset = extract_asset_info(prompt)
    
    # Merge asset
    existing_asset = segment.get("asset", {})
    if not existing_asset:
        existing_asset = extracted_asset
    else:
        # Ensure keys exist
        for k in ["characters", "scene", "props"]:
            if k not in existing_asset:
                existing_asset[k] = [] if k != "scene" else None
        
        if not existing_asset.get("scene") and extracted_asset["scene"]:
            existing_asset["scene"] = extracted_asset["scene"]
        if not existing_asset.get("characters") and extracted_asset["characters"]:
            # Append missing
            for c in extracted_asset["characters"]:
                if c not in existing_asset["characters"]:
                    existing_asset["characters"].append(c)

    new_seg = {
        "segment_index": segment.get("segment_index"),
        "prompt_text": prompt,
        "image_url": segment.get("image_url", TEMPLATE_FIELDS["image_url"]),
        "asset": existing_asset,
        "duration_seconds": segment.get("duration_seconds", TEMPLATE_FIELDS["duration_seconds"]),
        "is_pro": segment.get("is_pro", TEMPLATE_FIELDS["is_pro"]),
        "resolution": segment.get("resolution", TEMPLATE_FIELDS["resolution"]),
        "director_intent": segment.get("director_intent")
    }
    return new_seg

def process_file(file_path: Path):
    try:
        # Determine if source is MD or JSON
        if file_path.suffix == '.md':
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            json_str = extract_json_from_md(content)
            if not json_str:
                return
            data = json.loads(json_str)
            clean_name = file_path.stem.replace("[分镜-", "").replace("]", "")
            output_name = f"storyboard_{clean_name}.json"
            output_path = file_path.parent / output_name
            
        elif file_path.suffix == '.json':
            # Re-normalize existing JSON
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            output_path = file_path
            
        if "segments" not in data:
            return

        normalized_segments = [normalize_segment(seg) for seg in data["segments"]]
        
        new_data = {
            "_comment": f"Standardized via normalize_script",
            "segments": normalized_segments
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(new_data, f, indent=2, ensure_ascii=False)
            
        print(f"[OK] Normalized: {output_path}")

    except Exception as e:
        print(f"[ERROR] {file_path.name}: {e}")

def main():
    if not SOURCE_ROOT.exists():
        print(f"Source root not found: {SOURCE_ROOT}")
        return
    
    print(f"Scanning and Normalizing {SOURCE_ROOT}...")
    # Process both MD source and existing JSON to ensure alignment
    for root, dirs, files in os.walk(SOURCE_ROOT):
        for file in files:
            if file.startswith("storyboard_") and file.endswith(".json"):
                process_file(Path(root) / file)
            # Optional: re-generate from MD if needed, but JSON is now source of truth if exists

if __name__ == "__main__":
    main()
