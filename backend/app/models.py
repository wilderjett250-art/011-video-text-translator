from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class VideoMetadata(BaseModel):
    width: int
    height: int
    fps: float
    frame_count: int
    duration_sec: float
    has_audio: bool = False


class FrameAsset(BaseModel):
    id: str
    timestamp_sec: float
    frame_index: int
    path: str
    url: str


class Box(BaseModel):
    x: float = Field(ge=0, le=1)
    y: float = Field(ge=0, le=1)
    w: float = Field(gt=0, le=1)
    h: float = Field(gt=0, le=1)


class OverlayStyle(BaseModel):
    font_size: int = Field(default=34, ge=10, le=140)
    font_weight: str = "bold"
    text_color: str = "#ffffff"
    background_color: str = "#111111"
    background_opacity: float = Field(default=0.78, ge=0, le=1)
    padding: int = Field(default=10, ge=0, le=80)
    radius: int = Field(default=8, ge=0, le=80)
    align: str = "center"


class TextSegment(BaseModel):
    id: str
    start_time: float = Field(ge=0)
    end_time: float = Field(ge=0)
    source_text: str = ""
    translated_text: str
    box: Box
    style: OverlayStyle = Field(default_factory=OverlayStyle)
    locked: bool = False
    confidence: Optional[float] = None


class ProjectState(BaseModel):
    id: str
    name: str
    source_path: str
    source_filename: str
    created_at: str
    updated_at: str
    metadata: Optional[VideoMetadata] = None
    frames: List[FrameAsset] = Field(default_factory=list)
    segments: List[TextSegment] = Field(default_factory=list)
    output_path: Optional[str] = None
    output_url: Optional[str] = None
    notes: str = ""


class ImportPathRequest(BaseModel):
    path: str
    name: Optional[str] = None


class AnalyzeRequest(BaseModel):
    sample_count: int = Field(default=8, ge=3, le=24)


class SegmentListRequest(BaseModel):
    segments: List[TextSegment]


class RenderRequest(BaseModel):
    segments: Optional[List[TextSegment]] = None
    output_name: Optional[str] = None


class JobState(BaseModel):
    id: str
    kind: str
    status: str
    created_at: str
    updated_at: str
    progress: float = 0
    message: str = ""
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


def now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"

