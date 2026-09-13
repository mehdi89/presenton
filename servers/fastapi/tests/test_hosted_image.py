import base64
import unittest
from types import SimpleNamespace as N
from unittest.mock import AsyncMock
from utils.hosted_image import generate_hosted_image

PNG = b"\x89PNG\r\n\x1a\nfixture"
ITEM = N(type="response.output_item.done", item=N(type="image_generation_call", result=base64.b64encode(PNG).decode()))
DONE = N(type="response.completed", response=N(status="completed"))

class Stream:
    def __init__(self, events): self.events = events
    async def __aenter__(self): return self
    async def __aexit__(self, *args): pass
    async def __aiter__(self):
        for event in self.events: yield event

class HostedImageTest(unittest.IsolatedAsyncioTestCase):
    async def test_completed_item_survives_empty_final_output(self):
        client = N(responses=N(create=AsyncMock(return_value=Stream([ITEM, DONE]))))
        self.assertEqual(await generate_hosted_image(client, "gpt-5.6-luna", "garden"), PNG)
        self.assertEqual(client.responses.create.call_args.kwargs["reasoning"], {"effort": "low"})

    async def test_truncated_failed_incomplete_or_missing_image_rejected(self):
        for events in ([ITEM], [ITEM, N(type="response.failed")], [ITEM, N(type="response.incomplete")], [DONE]):
            with self.subTest(events=events):
                client = N(responses=N(create=AsyncMock(return_value=Stream(events))))
                with self.assertRaises(RuntimeError):
                    await generate_hosted_image(client, "gpt-5.6-luna", "garden")

if __name__ == "__main__": unittest.main()
