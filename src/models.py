from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator, model_validator
from pathlib import Path

class Segment(BaseModel):
    segment_index: int
    prompt_text: str
    # 附加图片 (可选) - 必须是公网可访问的 URL
    image_url: Optional[str] = None
    
    # 视频参数
    is_pro: bool = False
    duration_seconds: int = 10
    resolution: Literal["horizontal", "vertical"] = "horizontal"
    
    # Optional metadata
    director_intent: Optional[str] = None
    
    @model_validator(mode='after')
    def validate_duration_constraints(self):
        # 普通模式：10/15（默认10）
        # Pro模式：10/15/25（默认10）
        allowed_normal = [10, 15]
        allowed_pro = [10, 15, 25]
        
        if self.is_pro:
            if self.duration_seconds not in allowed_pro:
                raise ValueError(f"Pro Mode duration must be one of {allowed_pro}, got {self.duration_seconds}")
        else:
            if self.duration_seconds not in allowed_normal:
                raise ValueError(f"Normal Mode duration must be one of {allowed_normal}, got {self.duration_seconds}")
        return self

class Storyboard(BaseModel):
    segments: List[Segment]

class GenerationTask(BaseModel):
    """
    Represents a single video generation job (one version of a segment).
    """
    id: str
    source_file: Path
    segment: Segment
    version_index: int
    output_dir: Path
    
    @property
    def output_filename_base(self) -> str:
        return f"{self.segment.segment_index}_v{self.version_index}"
