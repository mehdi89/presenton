import json
import os
import unittest
from unittest.mock import patch, Mock, AsyncMock
from llmai.shared import JSONSchemaResponse, UserMessage
from utils.llm_utils import get_generate_kwargs, extract_structured_content, generate_structured_with_schema_retries
from llmai.shared.errors import LLMError
from types import SimpleNamespace

class ManagedSchemaTest(unittest.TestCase):
    def test_managed_schema_instruction_preserves_markdown_in_json(self):
        schema = {"type": "object", "properties": {"slides": {"type": "array", "items": {"type": "string"}}}, "required": ["slides"]}
        fmt = JSONSchemaResponse(name="outline", json_schema=schema, strict=False)
        messages = [UserMessage(content="Write a Markdown garden outline")]
        with patch.dict(os.environ, {"LLM": "litellm"}):
            managed = get_generate_kwargs("gpt-5.6-luna", messages, response_format=fmt)
            byok = get_generate_kwargs("other-model", messages, response_format=fmt)
            plain = get_generate_kwargs("gpt-5.6-luna", messages)
        self.assertEqual(len(managed["messages"]), 2)
        self.assertEqual(len(byok["messages"]), 1)
        self.assertEqual(len(plain["messages"]), 1)
        self.assertEqual(len(messages), 1)
        instruction = str(managed["messages"][-1].content)
        self.assertIn("do not return a bare Markdown", instruction)
        self.assertIn('"slides"', instruction)
        self.assertEqual(extract_structured_content('{"slides":["# Garden"]}'), {"slides": ["# Garden"]})



class StructuredParseRetryTest(unittest.IsolatedAsyncioTestCase):
    async def test_provider_parse_errors_retry_but_other_errors_propagate(self):
        malformed = json.JSONDecodeError("Expecting delimiter", "{", 1)
        for error in (malformed, LLMError(500, "parse failed", cause=malformed)):
            client = SimpleNamespace(generate=Mock(side_effect=[error, SimpleNamespace(content={"ok": True})]))
            with patch("utils.llm_utils.asyncio.sleep", new=AsyncMock()):
                result = await generate_structured_with_schema_retries(client, "test", messages=[], response_format=object(), json_schema={})
            self.assertEqual(result, {"ok": True})
            self.assertEqual(client.generate.call_count, 2)
        for error, attempts in ((LLMError(401, "unauthorized"), 1), (LLMError(500, "parse failed", cause=malformed), 3)):
            client = SimpleNamespace(generate=Mock(side_effect=error))
            with patch("utils.llm_utils.asyncio.sleep", new=AsyncMock()):
                with self.assertRaises(LLMError):
                    await generate_structured_with_schema_retries(client, "test", messages=[], response_format=object(), json_schema={})
            self.assertEqual(client.generate.call_count, attempts)

if __name__ == "__main__": unittest.main()
