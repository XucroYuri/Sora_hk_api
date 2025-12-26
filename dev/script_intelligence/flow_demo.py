import json
import re
from pathlib import Path
from typing import List, Dict, Any

# ==========================================
# 1. 模拟数据 (Mock Data)
# ==========================================

RAW_SCRIPT = """
SCENE 1 - CLASSROOM - DAY
小美走进教室，放下书本。她看起来很累。
同学们都在吵闹。
小美拍了拍桌子：“安静！”
大家安静了下来。王大锤推门进来。
"""

# Stage 1 Output (模拟 LLM 分析结果)
GLOBAL_CONTEXT = {
    "metadata": {
        "global_summary": "小美老师努力维持课堂秩序，直到问题学生王大锤出现。"
    },
    "character_bible": [
        {"name": "小美", "id": "@xiaomei", "aliases": ["她", "小美老师"]},
        {"name": "王大锤", "id": "@wang", "aliases": ["大锤"]}
    ]
}

# ==========================================
# 2. 核心逻辑类 (Core Logic)
# ==========================================

class ScriptIntelligenceEngine:
    def __init__(self, context: Dict[str, Any]):
        self.context = context
        self.bible = {c['name']: c['id'] for c in context['character_bible']}
    
    def split_script(self, text: str) -> List[str]:
        """
        简单切分逻辑：按换行符或场景头切分。
        实际项目中这里会更复杂（基于语义或正则）。
        """
        # Demo: Simply split by lines for granularity
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        return lines

    def process_chunk(self, chunk: str) -> Dict[str, Any]:
        """
        模拟 LLM 处理：将文本转化为 Segment。
        这里我们用简单的规则模拟 LLM 的“角色标记”行为。
        """
        print(f"\n[LLM Processing] Input Chunk: {chunk}")
        
        # 1. 模拟 Visual Translation & Marking
        # 简单替换：将名字包在 (( )) 里
        visual_prompt = chunk
        assets = []
        
        for name, char_id in self.bible.items():
            if name in visual_prompt:
                # 模拟 LLM 识别并标记
                visual_prompt = visual_prompt.replace(name, f"(( {name} ))")
                assets.append({"name": name, "id": char_id})
        
        # 2. 模拟 Dialogue Extraction
        dialogue = None
        match = re.search(r'“(.+?)”', chunk)
        if match:
            dialogue = match.group(0) # Keep quotes
        
        return {
            "prompt_text": visual_prompt,
            "dialogue": dialogue,
            "asset": {
                "characters": assets
            }
        }

    def run(self, raw_text: str):
        print(">>> Stage 1: Global Context Loaded")
        print(f"Bible: {list(self.bible.keys())}")
        
        print("\n>>> Stage 2: Splitting Script")
        chunks = self.split_script(raw_text)
        print(f"Generated {len(chunks)} chunks.")
        
        print("\n>>> Stage 3: Visual Adaptation (Simulated)")
        final_segments = []
        
        for i, chunk in enumerate(chunks):
            seg_data = self.process_chunk(chunk)
            seg_data["segment_index"] = i + 1
            final_segments.append(seg_data)
            
        return final_segments

# ==========================================
# 3. 执行入口
# ==========================================

if __name__ == "__main__":
    engine = ScriptIntelligenceEngine(GLOBAL_CONTEXT)
    result = engine.run(RAW_SCRIPT)
    
    # Output
    output_data = {
        "metadata": GLOBAL_CONTEXT['metadata'],
        "character_bible": GLOBAL_CONTEXT['character_bible'],
        "segments": result
    }
    
    print("\n>>> Final JSON Output:")
    print(json.dumps(output_data, indent=2, ensure_ascii=False))
