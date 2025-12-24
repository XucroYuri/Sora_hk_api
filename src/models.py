from typing import List, Optional, Literal
from pydantic import BaseModel, Field, model_validator
from pathlib import Path

class Asset(BaseModel):
    characters: List[str] = Field(default_factory=list, description="List of character names or IDs")
    scene: Optional[str] = None
    props: List[str] = Field(default_factory=list, description="List of props")

class Segment(BaseModel):
    segment_index: int
    prompt_text: str
    image_url: Optional[str] = None
    
    # New Asset Field
    asset: Optional[Asset] = Field(default_factory=lambda: Asset())

    # Video Params
    is_pro: bool = False
    duration_seconds: int = 10
    resolution: Literal["horizontal", "vertical"] = "horizontal"
    
    # Metadata
    director_intent: Optional[str] = None
    
    @model_validator(mode='after')
    def validate_segment_integrity(self):
        # 1. Validate Prompt
        if not self.prompt_text or not self.prompt_text.strip():
            raise ValueError("Prompt text cannot be empty.")

        # 2. Validate Duration
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
    _comment: Optional[str] = None

class GenerationTask(BaseModel):
    id: str
    source_file: Path
    segment: Segment
    version_index: int
    output_dir: Path
    
    @property
    def output_filename_base(self) -> str:
        return f"{self.segment.segment_index}_v{self.version_index}"