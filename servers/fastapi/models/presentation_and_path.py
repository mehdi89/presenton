from pydantic import BaseModel
from typing import Optional
import uuid


class UsageMetadata(BaseModel):
    """Token usage and cost tracking for presentation generation"""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    outline_generation_tokens: int = 0
    slide_generation_tokens: int = 0
    image_generation_count: int = 0
    total_cost_usd: float = 0.0


class PresentationAndPath(BaseModel):
    presentation_id: uuid.UUID
    path: str


class PresentationPathAndEditPath(PresentationAndPath):
    edit_path: str
    usage: Optional[UsageMetadata] = None
