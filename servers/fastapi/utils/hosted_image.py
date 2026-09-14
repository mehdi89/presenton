"""Collect a completed hosted image from the native Responses stream."""
import base64


async def generate_hosted_image(client, model: str, prompt: str) -> bytes:
    stream = await client.responses.create(
        model=model,
        input=[{"role": "user", "content": [{"type": "input_text", "text": prompt}]}],
        reasoning={"effort": "low"},
        tools=[{"type": "image_generation", "size": "1024x1024", "quality": "low"}],
        stream=True,
    )
    image = None
    completed = False
    async with stream:
        async for event in stream:
            if event.type == "response.output_item.done":
                item = event.item
                if item.type == "image_generation_call" and isinstance(item.result, str):
                    image = item.result
            elif event.type == "response.completed":
                completed = event.response.status == "completed"
            elif event.type in {"response.failed", "response.incomplete", "error"}:
                raise RuntimeError("Hosted image generation did not complete")
    if not completed or not image:
        raise RuntimeError("Hosted image generation returned no completed image")
    data = base64.b64decode(image, validate=True)
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise RuntimeError("Hosted image generation returned invalid PNG data")
    return data
