from datetime import datetime
from typing import Any, Dict, List, Optional, Literal

from pydantic import BaseModel, Field

from .task import Segment, Asset


class StoryboardSummary(BaseModel):
    id: str
    name: str
    created_at: datetime
    segment_count: int


class SegmentOut(Segment):
    id: str


class SegmentUpdate(BaseModel):
    prompt_text: Optional[str] = None
    director_intent: Optional[str] = None
    image_url: Optional[str] = None
    duration_seconds: Optional[int] = None
    resolution: Optional[Literal["horizontal", "vertical"]] = None
    is_pro: Optional[bool] = None
    asset: Optional[Asset] = None


class RunCreate(BaseModel):
    storyboard_id: str
    model_id: str
    routing_strategy: Optional[
        Literal["manual", "default", "failover", "weighted", "cost", "latency", "quota"]
    ] = "default"
    gen_count: int = Field(1, ge=1, le=10)
    concurrency: int = Field(1, ge=1, le=50)
    range: str
    output_mode: Literal["centralized", "in_place", "custom"]
    output_path: Optional[str] = None
    dry_run: bool = False
    force: bool = False


class RunOut(BaseModel):
    id: str
    status: Literal["queued", "running", "completed", "failed", "download_failed"]
    total_tasks: int
    completed: int = 0
    failed: int = 0
    download_failed: int = 0
    created_at: datetime


ErrorCode = Literal[
    "content_policy",
    "validation_error",
    "rate_limited",
    "timeout",
    "quota_exceeded",
    "unauthorized",
    "forbidden",
    "dependency_error",
    "server_error",
    "unknown_error",
    "download_failed",
    "no_provider",
]


class TaskOut(BaseModel):
    id: str
    status: Literal["queued", "running", "completed", "failed", "download_failed"]
    video_url: Optional[str] = None
    metadata_url: Optional[str] = None
    full_prompt: Optional[str] = None
    error_msg: Optional[str] = None
    error_code: Optional[ErrorCode] = None
    retryable: Optional[bool] = None
    segment_index: Optional[int] = None


ClientEventType = Literal["ui_error", "api_error", "task_error", "i18n_error"]
ClientEventSeverity = Literal["info", "warning", "error", "critical"]


class ClientEventIn(BaseModel):
    event_id: Optional[str] = None
    event_type: ClientEventType
    severity: Optional[ClientEventSeverity] = None
    timestamp: Optional[datetime] = None
    timezone: Optional[str] = None
    user_locale: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    status_code: Optional[int] = Field(None, ge=100, le=599)
    latency_ms: Optional[int] = Field(None, ge=0)
    run_id: Optional[str] = None
    task_id: Optional[str] = None
    provider_id: Optional[str] = None
    model_id: Optional[str] = None
    error_code: Optional[str] = None
    message: Optional[str] = None
    stack: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class ClientEventBatchIn(BaseModel):
    events: List[ClientEventIn] = Field(..., min_items=1, max_items=100)


class ClientEventAck(BaseModel):
    event_id: str
    received_at: datetime


class ClientEventBatchOut(BaseModel):
    count: int
    events: List[ClientEventAck]


class ProviderCapabilities(BaseModel):
    supports_image_to_video: bool
    supported_durations: List[int]
    supported_resolutions: List[Literal["horizontal", "vertical"]]
    supports_pro: bool


class ProviderOut(BaseModel):
    id: str
    display_name: str
    enabled: bool
    priority: int
    weight: int = 1
    supports_image_to_video: bool
    supported_durations: List[int]
    supported_resolutions: List[Literal["horizontal", "vertical"]]
    supports_pro: bool


class ProviderUpdate(BaseModel):
    display_name: Optional[str] = None
    enabled: Optional[bool] = None
    priority: Optional[int] = None
    weight: Optional[int] = None
    supports_image_to_video: Optional[bool] = None
    supported_durations: Optional[List[int]] = None
    supported_resolutions: Optional[List[Literal["horizontal", "vertical"]]] = None
    supports_pro: Optional[bool] = None


class PaginatedStoryboards(BaseModel):
    items: List[StoryboardSummary]
    page: int
    page_size: int
    total: int


class PaginatedSegments(BaseModel):
    items: List[SegmentOut]
    page: int
    page_size: int
    total: int


class PaginatedRuns(BaseModel):
    items: List[RunOut]
    page: int
    page_size: int
    total: int


class PaginatedTasks(BaseModel):
    items: List[TaskOut]
    page: int
    page_size: int
    total: int


class PaginatedProviders(BaseModel):
    items: List[ProviderOut]
    page: int
    page_size: int
    total: int


class ModelOut(BaseModel):
    id: str
    display_name: str
    description: Optional[str] = None
    enabled: bool = True


class ModelAdminOut(BaseModel):
    id: str
    display_name: str
    description: Optional[str] = None
    enabled: bool = True
    provider_map: Dict[str, List[str]] = Field(default_factory=dict)


class ModelUpdate(BaseModel):
    display_name: Optional[str] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None


class ModelProviderMapUpdate(BaseModel):
    provider_model_ids: List[str]


class PaginatedModels(BaseModel):
    items: List[ModelOut]
    page: int
    page_size: int
    total: int


class PaginatedAdminModels(BaseModel):
    items: List[ModelAdminOut]
    page: int
    page_size: int
    total: int
