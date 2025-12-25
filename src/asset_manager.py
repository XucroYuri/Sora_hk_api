import logging
from pathlib import Path
from typing import Optional, List, Literal

logger = logging.getLogger(__name__)

# Supported image extensions for lookup
IMAGE_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.webp', '.bmp']

class AssetManager:
    """
    Manages the 'asset' directory structure for a given Storyboard JSON file.
    
    Structure:
    {json_dir}/
    └── asset/
        ├── character/  # Images named after characters (e.g. "Alice.png")
        ├── scene/      # Images named after scenes
        ├── props/      # Images named after props
        └── segment/    # Segment reference images
    """
    
    def __init__(self, json_path: Path):
        self.json_path = json_path
        self.base_dir = json_path.parent / "asset"
        self.subdirs = {
            "character": self.base_dir / "character",
            "scene": self.base_dir / "scene",
            "props": self.base_dir / "props",
            "segment": self.base_dir / "segment"
        }

    def scaffold(self):
        """
        Creates the standardized asset directory structure if it doesn't exist.
        """
        try:
            if not self.base_dir.exists():
                self.base_dir.mkdir(parents=True)
                
            for path in self.subdirs.values():
                path.mkdir(exist_ok=True)
                
            # Create a .gitkeep or README to ensure git tracks it if empty? 
            # (Optional, skipping for now to keep it clean)
            
        except Exception as e:
            logger.error(f"Failed to scaffold asset directory for {self.json_path}: {e}")

    def _find_image(self, directory: Path, stem_name: str) -> Optional[Path]:
        """
        Helper to find an image file with various extensions.
        """
        # Sanitize filename (remove illegal chars if necessary, but assume mapped)
        # For now, we assume the user names the file exactly as the asset name.
        
        # 1. Exact match with extensions
        for ext in IMAGE_EXTENSIONS:
            candidate = directory / f"{stem_name}{ext}"
            if candidate.exists():
                return candidate
        return None

    def get_character_image(self, character_name: str) -> Optional[Path]:
        """
        Finds the character reference image.
        Format: "Name (@ID )" -> Search for "Name (@ID )" or just "Name"?
        
        Rule: We use the Full Name string as the filename identifier.
        If the JSON says "Alice @123", we look for "Alice @123.png".
        """
        # We strip the ID if desired, but user said "Filename same as Character Name".
        # If the Character Name in JSON includes the ID, we use it.
        # However, usually file systems prefer cleaner names. 
        # Let's try exact match first, then clean name match.
        
        # Strategy 1: Exact
        path = self._find_image(self.subdirs["character"], character_name.strip())
        if path: return path
        
        # Strategy 2: Clean name (remove @id)
        # "Alice @123" -> "Alice"
        if '@' in character_name:
            clean_name = character_name.split('@')[0].strip()
            path = self._find_image(self.subdirs["character"], clean_name)
            if path: return path
            
        return None

    def get_scene_image(self, scene_name: str) -> Optional[Path]:
        return self._find_image(self.subdirs["scene"], scene_name.strip())

    def get_prop_image(self, prop_name: str) -> Optional[Path]:
        return self._find_image(self.subdirs["props"], prop_name.strip())

    def get_segment_image(self, segment_index: int, type: Literal["start", "end", "grid"] = "start") -> Optional[Path]:
        """
        Retrieves segment-specific reference images.
        
        Naming Convention:
        - Start Frame: {index}_start.png
        - End Frame:   {index}_end.png
        - Grid:        {index}_grid.png
        """
        filename_base = f"{segment_index}_{type}"
        return self._find_image(self.subdirs["segment"], filename_base)

    def resolve_any_segment_ref(self, segment_index: int) -> Optional[Path]:
        """
        Returns the best available reference for a segment.
        Priority: Start > Grid > End
        """
        for t in ["start", "grid", "end"]:
            path = self.get_segment_image(segment_index, type=t) # type: ignore
            if path:
                return path
        return None
