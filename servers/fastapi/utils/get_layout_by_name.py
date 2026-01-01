import os
import aiohttp
from fastapi import HTTPException
from models.presentation_layout import PresentationLayoutModel
from typing import List

# Get client URL from environment variable
# For Docker on Mac/Windows use host.docker.internal
# For Docker on Linux use 172.17.0.1 (Docker bridge network)
CLIENT_URL = os.getenv("CLIENT_URL", "http://host.docker.internal:3000")

# Hardcoded templates to bypass Next.js dependency
HARDCODED_TEMPLATES = {
    "general": {
        "name": "general",
        "ordered": False,
        "slides": [
            {
                "id": "general:general-intro-slide",
                "name": "Intro Slide",
                "description": "A clean slide layout for introducing your presentation",
                "json_schema": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "minLength": 3, "maxLength": 40},
                        "description": {"type": "string", "minLength": 10, "maxLength": 150},
                        "presenterName": {"type": "string", "minLength": 2, "maxLength": 50},
                        "presentationDate": {"type": "string"},
                                "image": {
                            "type": "object",
                            "properties": {
                                "__image_url__": {"type": "string"},
                                "__image_prompt__": {"type": "string", "minLength": 10, "maxLength": 50}
                            },
                            "required": ["__image_prompt__"]
                        }
                    },
                    "required": ["title", "description"]
                }
            },
            {
                "id": "general:bullet-with-icons-slide",
                "name": "Bullet Points with Icons",
                "description": "Display bullet points with accompanying icons",
                "json_schema": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "minLength": 3, "maxLength": 40},
                        "description": {"type": "string", "maxLength": 150},
                        "image": {
                            "type": "object",
                            "properties": {
                                "__image_url__": {"type": "string"},
                                "__image_prompt__": {"type": "string", "minLength": 10, "maxLength": 50}
                            },
                            "required": ["__image_prompt__"]
                        },
                        "bulletPoints": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string", "minLength": 2, "maxLength": 60},
                                    "description": {"type": "string", "minLength": 10, "maxLength": 100},
                                    "icon": {
                                        "type": "object",
                                        "properties": {
                                            "__icon_url__": {"type": "string"},
                                            "__icon_query__": {"type": "string", "minLength": 5, "maxLength": 20}
                                        },
                                        "required": ["__icon_query__"]
                                    }
                                },
                                "required": ["title", "description"]
                            },
                            "minItems": 1,
                            "maxItems": 3
                        }
                    },
                    "required": ["title", "bulletPoints"]
                }
            },
            {
                "id": "general:numbered-bullets-slide",
                "name": "Numbered Bullets",
                "description": "Sequential steps or numbered points",
                "json_schema": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "minLength": 3, "maxLength": 50},
                        "bullets": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "text": {"type": "string", "minLength": 5, "maxLength": 150}
                                },
                                "required": ["text"]
                            },
                            "minItems": 2,
                            "maxItems": 8
                        }
                    },
                    "required": ["title", "bullets"]
                }
            },
            {
                "id": "general:quote-slide",
                "name": "Quote Slide",
                "description": "Highlight an important quote with attribution",
                "json_schema": {
                    "type": "object",
                    "properties": {
                        "quote": {"type": "string", "minLength": 10, "maxLength": 200},
                        "author": {"type": "string", "minLength": 2, "maxLength": 50},
                        "context": {"type": "string", "maxLength": 100}
                    },
                    "required": ["quote"]
                }
            },
            {
                "id": "general:metrics-slide",
                "name": "Metrics Slide",
                "description": "Display key metrics or statistics",
                "json_schema": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "minLength": 3, "maxLength": 50},
                        "metrics": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "value": {"type": "string", "minLength": 1, "maxLength": 20},
                                    "label": {"type": "string", "minLength": 2, "maxLength": 50}
                                },
                                "required": ["value", "label"]
                            },
                            "minItems": 2,
                            "maxItems": 4
                        }
                    },
                    "required": ["title", "metrics"]
                }
            },
            {
                "id": "general:table-of-contents-slide",
                "name": "Table of Contents",
                "description": "Outline the structure of your presentation",
                "json_schema": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "minLength": 3, "maxLength": 50},
                        "items": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "text": {"type": "string", "minLength": 3, "maxLength": 50}
                                },
                                "required": ["text"]
                            },
                            "minItems": 2,
                            "maxItems": 8
                        }
                    },
                    "required": ["title", "items"]
                }
            }
        ]
    },
    "modern": {
        "name": "modern",
        "ordered": False,
        "slides": [
            {
                "id": "modern:modern-intro-slide",
                "name": "Intro Slide",
                "description": "Modern introduction slide",
                "json_schema": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "minLength": 3, "maxLength": 40},
                        "description": {"type": "string", "minLength": 10, "maxLength": 150}
                    },
                    "required": ["title"]
                }
            },
            {
                "id": "modern:modern-bullet-points",
                "name": "Bullet Points",
                "description": "Modern bullet point layout",
                "json_schema": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "minLength": 3, "maxLength": 50},
                        "bullets": {
                            "type": "array",
                            "items": {"type": "string"},
                            "minItems": 2,
                            "maxItems": 6
                        }
                    },
                    "required": ["title", "bullets"]
                }
            }
        ]
    },
    "standard": {
        "name": "standard",
        "ordered": False,
        "slides": [
            {
                "id": "standard:standard-intro-slide",
                "name": "Intro Slide",
                "description": "Standard introduction slide",
                "json_schema": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "minLength": 3, "maxLength": 40},
                        "description": {"type": "string", "minLength": 10, "maxLength": 150}
                    },
                    "required": ["title"]
                }
            },
            {
                "id": "standard:standard-bullet-points",
                "name": "Bullet Points",
                "description": "Standard bullet point layout",
                "json_schema": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "minLength": 3, "maxLength": 50},
                        "bullets": {
                            "type": "array",
                            "items": {"type": "string"},
                            "minItems": 2,
                            "maxItems": 6
                        }
                    },
                    "required": ["title", "bullets"]
                }
            }
        ]
    },
    "swift": {
        "name": "swift",
        "ordered": False,
        "slides": [
            {
                "id": "swift:swift-intro-slide",
                "name": "Intro Slide",
                "description": "Swift introduction slide",
                "json_schema": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "minLength": 3, "maxLength": 40},
                        "description": {"type": "string", "minLength": 10, "maxLength": 150}
                    },
                    "required": ["title"]
                }
            },
            {
                "id": "swift:swift-bullet-points",
                "name": "Bullet Points",
                "description": "Swift bullet point layout",
                "json_schema": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "minLength": 3, "maxLength": 50},
                        "bullets": {
                            "type": "array",
                            "items": {"type": "string"},
                            "minItems": 2,
                            "maxItems": 6
                        }
                    },
                    "required": ["title", "bullets"]
                }
            }
        ]
    }
}

async def get_layout_by_name(layout_name: str) -> PresentationLayoutModel:
    """
    Get presentation layout by name.
    First checks hardcoded templates, then falls back to Next.js API if needed.
    """
    print(f"[get_layout_by_name] Requesting template: {layout_name}")

    # First check hardcoded templates
    if layout_name in HARDCODED_TEMPLATES:
        print(f"[get_layout_by_name] Using hardcoded template: {layout_name}")
        template_data = HARDCODED_TEMPLATES[layout_name]
        return PresentationLayoutModel(**template_data)

    # Fallback to Next.js fetch with timeout
    print(f"[get_layout_by_name] Template not in hardcoded list, trying Next.js API...")
    try:
        url = f"{CLIENT_URL}/api/template?group={layout_name}"
        print(f"[get_layout_by_name] Fetching from: {url}")

        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    layout_json = await response.json()
                    print(f"[get_layout_by_name] Successfully fetched template from Next.js")
                    return PresentationLayoutModel(**layout_json)
                else:
                    error_text = await response.text()
                    print(f"[get_layout_by_name] Next.js API returned {response.status}: {error_text}")
    except Exception as e:
        print(f"[get_layout_by_name] Failed to fetch from Next.js: {str(e)}")

    # If we get here, template not found anywhere
    available_templates = ", ".join(HARDCODED_TEMPLATES.keys())
    raise HTTPException(
        status_code=404,
        detail=f"Template '{layout_name}' not found. Available templates: {available_templates}"
    )
