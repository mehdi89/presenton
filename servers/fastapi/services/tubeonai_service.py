"""
TubeOnAI integration service for token deduction.

This service handles communication with the TubeOnAI backend to deduct tokens
after presentation content generation.
"""

import os
import httpx
from typing import Optional
from pydantic import BaseModel
from utils.usage_tracker import UsageTracker


class TokenDeductionMetadata(BaseModel):
    """Metadata for token deduction request"""
    model: str = "gpt-4o"
    tool_name: str = "slides"
    provider: str = "presenton"
    presentation_id: Optional[str] = None
    user_id: Optional[str] = None
    provider_model_id: Optional[str] = None
    async_flow: bool = False
    full_generation: bool = True
    image_count: int = 0


class TokenDeductionRequest(BaseModel):
    """Request payload for TubeOnAI token deduction API"""
    tokens: int
    input_tokens: int
    output_tokens: int
    feature_name: str = "custom_prompt"
    source: str = "video"  # "video", "collection", "article", "pdf"
    content_id: str
    description: str = "Presenton presentation generation"
    metadata: TokenDeductionMetadata


class TokenDeductionResponse(BaseModel):
    """Response from TubeOnAI token deduction API"""
    success: bool
    credits_deducted: Optional[int] = None
    tokens_processed: Optional[int] = None
    error: Optional[str] = None
    message: Optional[str] = None


class TubeOnAIService:
    """Service for integrating with TubeOnAI backend"""

    def __init__(self):
        # TubeOnAI API base URL - can be configured via environment variable
        self.api_base_url = os.environ.get(
            "TUBEONAI_API_BASE_URL",
            "https://api.tubeonai.com/api"
        )
        self.timeout = 30.0  # 30 seconds timeout

    async def deduct_tokens(
        self,
        auth_token: str,
        content_id: str,
        source: str,
        usage_tracker: UsageTracker,
        presentation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        provider_model_id: Optional[str] = None,
        model: str = "gpt-4o",
    ) -> TokenDeductionResponse:
        """
        Deduct tokens from user's TubeOnAI credit balance.

        Args:
            auth_token: User's authentication token
            content_id: ID of the content (summary/collection) being processed
            source: Source type ("video", "collection", etc.)
            usage_tracker: UsageTracker instance with token usage data
            presentation_id: ID of the generated presentation
            user_id: User ID
            provider_model_id: Provider model ID
            model: Model name used for generation

        Returns:
            TokenDeductionResponse with result
        """
        try:
            # Get usage metadata from tracker
            usage = usage_tracker.to_metadata()

            # Build metadata
            metadata = TokenDeductionMetadata(
                model=model,
                tool_name="slides",
                provider="presenton",
                presentation_id=presentation_id,
                user_id=user_id,
                provider_model_id=provider_model_id,
                async_flow=False,
                full_generation=True,
                image_count=usage.image_generation_count,
            )

            # Build request payload
            request_payload = {
                "tokens": usage.total_tokens,
                "input_tokens": usage.input_tokens,
                "output_tokens": usage.output_tokens,
                "feature_name": "custom_prompt",
                "source": source,
                "content_id": content_id,
                "description": f"Presenton full presentation generation ({usage.image_generation_count} images)",
                "metadata": metadata.model_dump(),
            }

            # Clean auth token
            clean_token = auth_token.replace("Bearer ", "")

            # Make request to TubeOnAI
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.api_base_url}/v3/credits/deduct",
                    json=request_payload,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {clean_token}",
                    },
                )

                if response.status_code == 200:
                    data = response.json()
                    return TokenDeductionResponse(
                        success=data.get("success", True),
                        credits_deducted=data.get("credits_deducted"),
                        tokens_processed=data.get("tokens_processed"),
                        message=data.get("message"),
                    )
                else:
                    error_msg = f"Token deduction failed with status {response.status_code}"
                    try:
                        error_data = response.json()
                        error_msg = error_data.get("message", error_data.get("error", error_msg))
                    except Exception:
                        pass

                    print(f"[TubeOnAI] Token deduction error: {error_msg}")
                    return TokenDeductionResponse(
                        success=False,
                        error=error_msg,
                    )

        except httpx.TimeoutException:
            print("[TubeOnAI] Token deduction timed out")
            return TokenDeductionResponse(
                success=False,
                error="Token deduction request timed out",
            )
        except Exception as e:
            print(f"[TubeOnAI] Token deduction error: {str(e)}")
            return TokenDeductionResponse(
                success=False,
                error=str(e),
            )

    def map_source_type(self, source_type: str) -> str:
        """Map source type to TubeOnAI expected values"""
        mapping = {
            "summary": "video",
            "collection": "collection",
            "channel": "collection",
            "video": "video",
            "article": "article",
            "pdf": "pdf",
        }
        return mapping.get(source_type.lower(), "video")


# Global singleton instance
TUBEONAI_SERVICE = TubeOnAIService()
