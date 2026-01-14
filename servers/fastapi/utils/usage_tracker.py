"""Usage tracking utility for LLM API calls"""
from typing import Optional, Dict, Any
from models.presentation_and_path import UsageMetadata


class UsageTracker:
    """Tracks token usage across multiple LLM API calls"""

    def __init__(self):
        self.input_tokens = 0
        self.output_tokens = 0
        self.outline_generation_tokens = 0
        self.slide_generation_tokens = 0
        self.image_generation_count = 0
        self.total_cost_usd = 0.0

    def add_usage(
        self,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cost_usd: float = 0.0,
        phase: str = "general"
    ):
        """
        Add usage from an LLM API call

        Args:
            input_tokens: Number of input/prompt tokens
            output_tokens: Number of output/completion tokens
            cost_usd: Cost in USD for this call
            phase: Phase of generation (outline, slide, image)
        """
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.total_cost_usd += cost_usd

        total = input_tokens + output_tokens
        if phase == "outline":
            self.outline_generation_tokens += total
        elif phase == "slide":
            self.slide_generation_tokens += total
        elif phase == "image":
            self.image_generation_count += 1

    def extract_openai_usage(self, response: Any, phase: str = "general") -> None:
        """Extract usage from OpenAI API response"""
        if hasattr(response, 'usage') and response.usage:
            usage = response.usage
            input_tokens = getattr(usage, 'prompt_tokens', 0)
            output_tokens = getattr(usage, 'completion_tokens', 0)
            self.add_usage(input_tokens, output_tokens, phase=phase)

    def extract_anthropic_usage(self, response: Any, phase: str = "general") -> None:
        """Extract usage from Anthropic API response"""
        if hasattr(response, 'usage') and response.usage:
            usage = response.usage
            input_tokens = getattr(usage, 'input_tokens', 0)
            output_tokens = getattr(usage, 'output_tokens', 0)
            self.add_usage(input_tokens, output_tokens, phase=phase)

    def extract_google_usage(self, response: Any, phase: str = "general") -> None:
        """Extract usage from Google Gemini API response"""
        if hasattr(response, 'usage_metadata') and response.usage_metadata:
            usage = response.usage_metadata
            input_tokens = getattr(usage, 'prompt_token_count', 0)
            output_tokens = getattr(usage, 'candidates_token_count', 0)
            self.add_usage(input_tokens, output_tokens, phase=phase)

    def estimate_tokens(self, text: str, multiplier: float = 1.3) -> int:
        """
        Estimate tokens from text

        Args:
            text: Text to estimate tokens for
            multiplier: Multiplier for word count (default 1.3 accounts for tokens being ~0.75 words)

        Returns:
            Estimated token count
        """
        words = len(text.split())
        return int(words * multiplier)

    def to_metadata(self) -> UsageMetadata:
        """Convert to UsageMetadata model"""
        return UsageMetadata(
            input_tokens=self.input_tokens,
            output_tokens=self.output_tokens,
            total_tokens=self.input_tokens + self.output_tokens,
            outline_generation_tokens=self.outline_generation_tokens,
            slide_generation_tokens=self.slide_generation_tokens,
            image_generation_count=self.image_generation_count,
            total_cost_usd=self.total_cost_usd
        )
