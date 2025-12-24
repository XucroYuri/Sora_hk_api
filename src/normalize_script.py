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
    # Try regex for code block
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
    """
    Parses prompt_text to extract asset info based on specific patterns.
    Pattern Example: "...；场景：教室；..." or "...@wangdali_cc..."
    """
    asset = {
        "characters": [],
        "scene": None,
        "props": []
    }
    
    if not prompt_text:
        return asset

    # 1. Extract Scene (场景：XXX；)
    scene_match = re.search(r'[;；]\s*场景[：:]\s*(.*?)[;；]', prompt_text)
    if scene_match:
        asset["scene"] = scene_match.group(1).strip()

    # 2. Extract Characters with ID (@username)
    # Finding patterns like: "王大力 @wangdali_cc"
    # Regex: (\S+)\s+(@[a-zA-Z0-9_]+)
    char_matches = re.findall(r'([\u4e00-\u9fa5]+)\s*(@[a-zA-Z0-9_]+)', prompt_text)
    for name, char_id in char_matches:
        full_char = f"{name} {char_id}"
        if full_char not in asset["characters"]:
            asset["characters"].append(full_char)
            
    # 3. Props (Placeholder, hard to extract via regex unless tagged)
    
    return asset

def normalize_segment(segment):
    prompt = segment.get("prompt_text", "")
    
    # Auto-extract asset info
    extracted_asset = extract_asset_info(prompt)
    
    # Merge with existing asset if any (rare in md source)
    existing_asset = segment.get("asset", {})
    if not existing_asset:
        existing_asset = extracted_asset
    else:
        # Simple merge: prefer extracted if missing
        if not existing_asset.get("scene") and extracted_asset["scene"]:
            existing_asset["scene"] = extracted_asset["scene"]
        if not existing_asset.get("characters") and extracted_asset["characters"]:
            existing_asset["characters"] = extracted_asset["characters"]

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
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        json_str = extract_json_from_md(content)
        if not json_str:
            print(f"[SKIP] No JSON found in {file_path.name}")
            return

        data = json.loads(json_str)
        if "segments" not in data:
            return

        normalized_segments = [normalize_segment(seg) for seg in data["segments"]]
        
        new_data = {
            "_comment": f"Generated from {file_path.name}",
            "segments": normalized_segments
        }

        clean_name = file_path.stem.replace("[分镜-", "").replace("]", "")
        output_name = f"storyboard_{clean_name}.json"
        output_path = file_path.parent / output_name

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(new_data, f, indent=2, ensure_ascii=False)
            
        print(f"[OK] Generated: {output_path}")

    except Exception as e:
        print(f"[ERROR] {file_path.name}: {e}")

def main():
    if not SOURCE_ROOT.exists():
        print(f"Source root not found: {SOURCE_ROOT}")
        return
    
    print(f"Scanning {SOURCE_ROOT}...")
    for root, dirs, files in os.walk(SOURCE_ROOT):
        for file in files:
            if file.startswith("[分镜-") and file.endswith(".md"):
                process_file(Path(root) / file)

if __name__ == "__main__":
    main()