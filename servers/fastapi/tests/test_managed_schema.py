import json
import os
import unittest
from unittest.mock import patch
from llmai.shared import JSONSchemaResponse, UserMessage
from utils.llm_utils import get_generate_kwargs, extract_structured_content

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

if __name__ == "__main__": unittest.main()
