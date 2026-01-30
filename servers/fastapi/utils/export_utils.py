import json
import os
import re
import aiohttp
from typing import Literal
import uuid
from fastapi import HTTPException
from pathvalidate import sanitize_filename
from urllib.parse import quote

from models.pptx_models import PptxPresentationModel
from models.presentation_and_path import PresentationAndPath
from services.pptx_presentation_creator import PptxPresentationCreator
from services.temp_file_service import TEMP_FILE_SERVICE
from utils.asset_directory_utils import get_exports_directory


def clean_filename(title: str) -> str:
    """Sanitize and clean a filename for safe filesystem and URL use."""
    sanitized = sanitize_filename(title or str(uuid.uuid4()))
    # Remove commas, semicolons, and other problematic characters
    sanitized = re.sub(r'[,;\'\"&]', '', sanitized)
    # Replace spaces and multiple underscores with single underscore
    sanitized = re.sub(r'[\s_]+', '_', sanitized).strip('_')
    if not sanitized:
        sanitized = "presentation"
    return sanitized


async def export_presentation(
    presentation_id: uuid.UUID, title: str, export_as: Literal["pptx", "pdf"]
) -> PresentationAndPath:
    if export_as == "pptx":

        # Get the converted PPTX model from the Next.js service
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"http://localhost/api/presentation_to_pptx_model?id={presentation_id}"
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    print(f"Failed to get PPTX model: {error_text}")
                    raise HTTPException(
                        status_code=500,
                        detail="Failed to convert presentation to PPTX model",
                    )
                pptx_model_data = await response.json()

        # Create PPTX file using the converted model
        pptx_model = PptxPresentationModel(**pptx_model_data)
        temp_dir = TEMP_FILE_SERVICE.create_temp_dir()
        pptx_creator = PptxPresentationCreator(pptx_model, temp_dir)
        await pptx_creator.create_ppt()

        export_directory = get_exports_directory()
        cleaned_title = clean_filename(title)
        filename = f"{cleaned_title}_{uuid.uuid4().hex[:8]}.pptx"
        pptx_path = os.path.join(
            export_directory,
            filename,
        )
        pptx_creator.save(pptx_path)

        # Return download URL with URL-encoded filename
        download_url = f"/api/download/{quote(filename)}"

        return PresentationAndPath(
            presentation_id=presentation_id,
            path=download_url,
        )
    else:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost/api/export-as-pdf",
                json={
                    "id": str(presentation_id),
                    "title": clean_filename(title),
                },
            ) as response:
                response_json = await response.json()

        return PresentationAndPath(
            presentation_id=presentation_id,
            path=response_json["path"],
        )
