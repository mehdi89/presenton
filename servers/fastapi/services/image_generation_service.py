import asyncio
import base64
import io
import json
import os
import aiohttp
from fastapi import HTTPException
from google import genai
from openai import NOT_GIVEN, AsyncOpenAI
from models.image_prompt import ImagePrompt
from models.sql.image_asset import ImageAsset
from services.blob_storage_service import get_blob_storage_service
from utils.get_env import (
    get_azure_openai_api_key_env,
    get_azure_openai_endpoint_env,
    get_azure_openai_deployment_name_env,
    get_azure_openai_api_version_env,
    get_azure_flux_api_key_env,
    get_azure_flux_endpoint_env,
    get_azure_flux_deployment_name_env,
    get_azure_flux_api_version_env,
    get_azure_flux_model_env,
    get_dall_e_3_quality_env,
    get_gpt_image_1_5_quality_env,
    get_pexels_api_key_env,
)
from utils.get_env import get_pixabay_api_key_env
from utils.get_env import get_comfyui_url_env
from utils.get_env import get_comfyui_workflow_env
from utils.image_provider import (
    is_azure_dalle_selected,
    is_azure_flux_selected,
    is_gpt_image_1_5_selected,
    is_image_generation_disabled,
    is_pixels_selected,
    is_pixabay_selected,
    is_gemini_flash_selected,
    is_nanobanana_pro_selected,
    is_dalle3_selected,
    is_comfyui_selected,
)
from models.azure_model_config import is_azure_dalle_model
import uuid


class ImageGenerationService:
    def __init__(self, output_directory: str):
        self.output_directory = output_directory
        self.is_image_generation_disabled = is_image_generation_disabled()
        self.image_gen_func = self.get_image_gen_func()
        self.blob_storage = get_blob_storage_service()

    def get_image_gen_func(self):
        if self.is_image_generation_disabled:
            return None

        if is_pixabay_selected():
            return self.get_image_from_pixabay
        elif is_pixels_selected():
            return self.get_image_from_pexels
        elif is_gemini_flash_selected():
            return self.generate_image_gemini_flash
        elif is_nanobanana_pro_selected():
            return self.generate_image_nanobanana_pro
        elif is_dalle3_selected():
            return self.generate_image_openai_dalle3
        elif is_gpt_image_1_5_selected():
            return self.generate_image_openai_gpt_image_1_5
        elif is_azure_dalle_selected():
            return self.generate_image_azure_dalle
        elif is_azure_flux_selected():
            return self.generate_image_azure_flux
        elif is_comfyui_selected():
            return self.generate_image_comfyui
        return None

    def is_stock_provider_selected(self):
        return is_pixels_selected() or is_pixabay_selected()

    async def generate_image(self, prompt: ImagePrompt) -> str | ImageAsset:
        """
        Generates an image based on the provided prompt.
        - If no image generation function is available, returns a placeholder image.
        - If the stock provider is selected, it uses the prompt directly,
        otherwise it uses the full image prompt with theme.
        - Output Directory is used for saving the generated image not the stock provider.
        - If Azure Blob Storage is configured, images are uploaded there and URLs returned.
        """
        if self.is_image_generation_disabled:
            print("Image generation is disabled. Using placeholder image.")
            return "/static/images/placeholder.jpg"

        if not self.image_gen_func:
            print("No image generation function found. Using placeholder image.")
            return "/static/images/placeholder.jpg"

        image_prompt = prompt.get_image_prompt(
            with_theme=not self.is_stock_provider_selected()
        )
        print(f"Request - Generating Image for {image_prompt}")

        try:
            if self.is_stock_provider_selected():
                image_path = await self.image_gen_func(image_prompt)
            else:
                image_path = await self.image_gen_func(
                    image_prompt, self.output_directory
                )
            if image_path:
                # Blob URLs and stock provider URLs are returned directly
                if image_path.startswith("http"):
                    return image_path
                # Local file paths are wrapped in ImageAsset for database tracking
                elif os.path.exists(image_path):
                    return ImageAsset(
                        path=image_path,
                        is_uploaded=False,
                        extras={
                            "prompt": prompt.prompt,
                            "theme_prompt": prompt.theme_prompt,
                        },
                    )
            raise Exception(f"Image not found at {image_path}")

        except Exception as e:
            print(f"Error generating image: {e}")
            return "/static/images/placeholder.jpg"

    async def generate_image_openai(
        self, prompt: str, output_directory: str, model: str, quality: str
    ) -> str:
        client = AsyncOpenAI()
        result = await client.images.generate(
            model=model,
            prompt=prompt,
            n=1,
            quality=quality,
            response_format="b64_json" if model == "dall-e-3" else NOT_GIVEN,
            size="1024x1024",
        )
        image_data = base64.b64decode(result.data[0].b64_json)

        # Upload to blob storage if configured, otherwise save locally
        if self.blob_storage.is_enabled:
            blob_url = self.blob_storage.upload_bytes(image_data, extension="png")
            print(f"Uploaded image to blob storage: {blob_url}")
            return blob_url

        image_path = os.path.join(output_directory, f"{uuid.uuid4()}.png")
        with open(image_path, "wb") as f:
            f.write(image_data)
        return image_path

    async def generate_image_openai_dalle3(
        self, prompt: str, output_directory: str
    ) -> str:
        return await self.generate_image_openai(
            prompt,
            output_directory,
            "dall-e-3",
            get_dall_e_3_quality_env() or "standard",
        )

    async def generate_image_openai_gpt_image_1_5(
        self, prompt: str, output_directory: str
    ) -> str:
        return await self.generate_image_openai(
            prompt,
            output_directory,
            "gpt-image-1.5",
            get_gpt_image_1_5_quality_env() or "medium",
        )

    async def generate_image_azure_dalle(
        self, prompt: str, output_directory: str
    ) -> str:
        """
        Generate image using Azure OpenAI DALL-E.

        Azure OpenAI only supports DALL-E models for image generation.
        Reference: https://go.microsoft.com/fwlink/?linkid=2197993
        """
        # Get Azure configuration
        api_key = get_azure_openai_api_key_env()
        endpoint = get_azure_openai_endpoint_env()
        deployment_name = get_azure_openai_deployment_name_env()
        api_version = get_azure_openai_api_version_env()

        if not api_key or not endpoint or not deployment_name:
            raise ValueError(
                "Azure OpenAI configuration is incomplete. Please set "
                "AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, and AZURE_OPENAI_DEPLOYMENT_NAME"
            )

        # Validate that deployment is a DALL-E model
        if not is_azure_dalle_model(deployment_name):
            raise ValueError(
                f"Azure OpenAI image generation only supports DALL-E models. "
                f"The deployment '{deployment_name}' is not a supported DALL-E model. "
                f"Please use a DALL-E 2 or DALL-E 3 deployment for image generation. "
                f"Learn more: https://go.microsoft.com/fwlink/?linkid=2197993"
            )

        # Create Azure OpenAI client
        from openai import AsyncOpenAI

        azure_client = AsyncOpenAI(
            api_key=api_key,
            base_url=f"{endpoint.rstrip('/')}/openai/deployments/{deployment_name}",
            default_query={"api-version": api_version},
            default_headers={"api-key": api_key},
        )

        # Determine quality based on model
        quality = get_dall_e_3_quality_env() or "standard"

        result = await azure_client.images.generate(
            model=deployment_name,
            prompt=prompt,
            n=1,
            quality=quality if "dall-e-3" in deployment_name.lower() else NOT_GIVEN,
            response_format="b64_json",
            size="1024x1024",
        )

        image_data = base64.b64decode(result.data[0].b64_json)

        # Upload to blob storage if configured, otherwise save locally
        if self.blob_storage.is_enabled:
            blob_url = self.blob_storage.upload_bytes(image_data, extension="png")
            print(f"Uploaded Azure DALL-E image to blob storage: {blob_url}")
            return blob_url

        image_path = os.path.join(output_directory, f"{uuid.uuid4()}.png")
        with open(image_path, "wb") as f:
            f.write(image_data)
        print(f"Generated Azure DALL-E image: {image_path}")
        return image_path

    async def generate_image_azure_flux(
        self, prompt: str, output_directory: str
    ) -> str:
        """
        Generate image using Azure FLUX-1.1-pro.

        FLUX is a high-quality image generation model hosted on Azure.
        It generates images in PNG format with base64 encoding.

        Note: Unlike deployment-based models, FLUX uses the /openai/v1/images/generations endpoint
        directly without deployment-specific routing.
        """
        # Get Azure FLUX configuration
        api_key = get_azure_flux_api_key_env()
        endpoint = get_azure_flux_endpoint_env()
        model_name = get_azure_flux_model_env() or "FLUX-1.1-pro"

        if not api_key or not endpoint:
            raise ValueError(
                "Azure FLUX configuration is incomplete. Please set "
                "AZURE_FLUX_API_KEY and AZURE_FLUX_ENDPOINT"
            )

        # Build request payload matching web-app-v2 implementation
        payload = {
            "prompt": prompt,
            "output_format": "png",
            "n": 1,
            "size": "1024x1024",
            "model": model_name,
        }

        # Make direct HTTP request to Azure FLUX endpoint
        # Uses /openai/v1/images/generations (NOT deployment-based endpoint)
        url = f"{endpoint.rstrip('/')}/openai/v1/images/generations"
        headers = {
            "Content-Type": "application/json",
            "api-key": api_key,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise HTTPException(
                        status_code=response.status,
                        detail=f"Azure FLUX API error: {error_text}",
                    )

                data = await response.json()
                base64_data = data.get("data", [{}])[0].get("b64_json")

                if not base64_data:
                    raise ValueError("No base64 data in Azure FLUX response")

                image_data = base64.b64decode(base64_data)

        # Upload to blob storage if configured, otherwise save locally
        if self.blob_storage.is_enabled:
            blob_url = self.blob_storage.upload_bytes(image_data, extension="png")
            print(f"Uploaded Azure FLUX image to blob storage: {blob_url}")
            return blob_url

        image_path = os.path.join(output_directory, f"{uuid.uuid4()}.png")
        with open(image_path, "wb") as f:
            f.write(image_data)
        print(f"Generated Azure FLUX image: {image_path}")
        return image_path

    async def _generate_image_google(
        self, prompt: str, output_directory: str, model: str
    ) -> str:
        """Base method for Google image generation models."""
        client = genai.Client()
        response = await asyncio.to_thread(
            client.models.generate_content,
            model=model,
            contents=[prompt],
        )

        image_path = None
        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                image = part.as_image()

                # Upload to blob storage if configured
                if self.blob_storage.is_enabled:
                    # Save to bytes buffer first
                    buffer = io.BytesIO()
                    image.save(buffer, format="JPEG")
                    buffer.seek(0)
                    blob_url = self.blob_storage.upload_bytes(
                        buffer.read(), extension="jpg"
                    )
                    print(f"Uploaded image to blob storage: {blob_url}")
                    return blob_url

                # Otherwise save locally
                image_path = os.path.join(output_directory, f"{uuid.uuid4()}.jpg")
                image.save(image_path)

        if not image_path:
            raise HTTPException(
                status_code=500, detail=f"No image generated by google {model}"
            )

        return image_path

    async def generate_image_gemini_flash(
        self, prompt: str, output_directory: str
    ) -> str:
        """Generate image using Gemini Flash (gemini-2.5-flash-image-preview)."""
        return await self._generate_image_google(
            prompt, output_directory, "gemini-2.5-flash-image-preview"
        )

    async def generate_image_nanobanana_pro(
        self, prompt: str, output_directory: str
    ) -> str:
        """Generate image using NanoBanana Pro (gemini-3-pro-image-preview)."""
        return await self._generate_image_google(
            prompt, output_directory, "gemini-3-pro-image-preview"
        )

    async def get_image_from_pexels(self, prompt: str) -> str:
        async with aiohttp.ClientSession(trust_env=True) as session:
            response = await session.get(
                f"https://api.pexels.com/v1/search?query={prompt}&per_page=1",
                headers={"Authorization": f"{get_pexels_api_key_env()}"},
            )
            data = await response.json()
            image_url = data["photos"][0]["src"]["large"]
            return image_url

    async def get_image_from_pixabay(self, prompt: str) -> str:
        async with aiohttp.ClientSession(trust_env=True) as session:
            response = await session.get(
                f"https://pixabay.com/api/?key={get_pixabay_api_key_env()}&q={prompt}&image_type=photo&per_page=3"
            )
            data = await response.json()
            image_url = data["hits"][0]["largeImageURL"]
            return image_url

    async def generate_image_comfyui(self, prompt: str, output_directory: str) -> str:
        """
        Generate image using ComfyUI workflow API.

        User provides:
        - COMFYUI_URL: ComfyUI server URL (e.g., http://192.168.1.7:8188)
        - COMFYUI_WORKFLOW: Workflow JSON exported from ComfyUI

        The workflow should have a CLIPTextEncode node with "Positive" in the title
        where the prompt will be injected.

        Args:
            prompt: The text prompt for image generation
            output_directory: Directory to save the generated image

        Returns:
            Path to the generated image file
        """
        comfyui_url = get_comfyui_url_env()
        workflow_json = get_comfyui_workflow_env()

        if not comfyui_url:
            raise ValueError("COMFYUI_URL environment variable is not set")

        if not workflow_json:
            raise ValueError(
                "COMFYUI_WORKFLOW environment variable is not set. Please provide a ComfyUI workflow JSON."
            )

        # Ensure URL doesn't have trailing slash
        comfyui_url = comfyui_url.rstrip("/")

        # Parse the workflow JSON
        try:
            workflow = json.loads(workflow_json)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid workflow JSON: {str(e)}")

        # Find and update the positive prompt node
        workflow = self._inject_prompt_into_workflow(workflow, prompt)

        async with aiohttp.ClientSession(trust_env=True) as session:
            # Step 1: Submit workflow
            prompt_id = await self._submit_comfyui_workflow(
                session, comfyui_url, workflow
            )

            # Step 2: Wait for completion
            status_data = await self._wait_for_comfyui_completion(
                session, comfyui_url, prompt_id
            )

            # Step 3: Download the generated image
            image_path = await self._download_comfyui_image(
                session, comfyui_url, status_data, prompt_id, output_directory
            )

            return image_path

    def _inject_prompt_into_workflow(self, workflow: dict, prompt: str) -> dict:
        """
        Find the prompt node in the workflow and inject the prompt text.
        Looks for a node with title 'Input Prompt' (case-insensitive).

        User must rename their prompt node to 'Input Prompt' in ComfyUI.
        """
        for node_id, node_data in workflow.items():
            meta = node_data.get("_meta", {})
            title = meta.get("title", "").lower()

            if title == "input prompt":
                if "inputs" in node_data and "text" in node_data["inputs"]:
                    node_data["inputs"]["text"] = prompt
                    print(
                        f"Injected prompt into node {node_id}: {meta.get('title', '')}"
                    )
                    return workflow

        raise ValueError(
            "Could not find a node with title 'Input Prompt' in the workflow. Please rename your prompt node to 'Input Prompt' in ComfyUI."
        )

    async def _submit_comfyui_workflow(
        self, session: aiohttp.ClientSession, comfyui_url: str, workflow: dict
    ) -> str:
        """Submit workflow to ComfyUI and return the prompt_id."""
        client_id = str(uuid.uuid4())
        payload = {"prompt": workflow, "client_id": client_id}

        response = await session.post(
            f"{comfyui_url}/prompt",
            json=payload,
            timeout=aiohttp.ClientTimeout(total=30),
        )

        if response.status != 200:
            error_text = await response.text()
            raise Exception(f"Failed to submit workflow to ComfyUI: {error_text}")

        data = await response.json()
        prompt_id = data.get("prompt_id")

        if not prompt_id:
            raise Exception("No prompt_id returned from ComfyUI")

        print(f"ComfyUI workflow submitted. Prompt ID: {prompt_id}")
        return prompt_id

    async def _wait_for_comfyui_completion(
        self,
        session: aiohttp.ClientSession,
        comfyui_url: str,
        prompt_id: str,
        timeout: int = 300,
        poll_interval: int = 4,
    ) -> dict:
        """Poll ComfyUI history endpoint until workflow completes."""
        start_time = asyncio.get_event_loop().time()

        while True:
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > timeout:
                raise Exception(f"ComfyUI workflow timed out after {timeout} seconds")

            await asyncio.sleep(poll_interval)

            response = await session.get(
                f"{comfyui_url}/history/{prompt_id}",
                timeout=aiohttp.ClientTimeout(total=30),
            )

            if response.status != 200:
                continue

            try:
                status_data = await response.json()
            except Exception as _:
                continue

            if prompt_id in status_data:
                execution_data = status_data[prompt_id]

                # Check for completion
                if "status" in execution_data:
                    status = execution_data["status"]
                    if status.get("completed", False):
                        print("ComfyUI workflow completed successfully")
                        return status_data
                    if "error" in status:
                        raise Exception(f"ComfyUI workflow error: {status['error']}")

                # Also check if outputs exist (alternative completion check)
                if "outputs" in execution_data and execution_data["outputs"]:
                    print("ComfyUI workflow completed (outputs found)")
                    return status_data

            print(f"Waiting for ComfyUI workflow... ({int(elapsed)}s)")

    async def _download_comfyui_image(
        self,
        session: aiohttp.ClientSession,
        comfyui_url: str,
        status_data: dict,
        prompt_id: str,
        output_directory: str,
    ) -> str:
        """Download the generated image from ComfyUI."""
        if prompt_id not in status_data:
            raise Exception("Prompt ID not found in status data")

        outputs = status_data[prompt_id].get("outputs", {})

        if not outputs:
            raise Exception("No outputs found in ComfyUI response")

        # Find the first image in outputs
        for node_id, node_output in outputs.items():
            if "images" in node_output:
                for image_info in node_output["images"]:
                    filename = image_info["filename"]
                    subfolder = image_info.get("subfolder", "")

                    # Build view params
                    params = {"filename": filename, "type": "output"}
                    if subfolder:
                        params["subfolder"] = subfolder

                    # Download the image
                    response = await session.get(
                        f"{comfyui_url}/view",
                        params=params,
                        timeout=aiohttp.ClientTimeout(total=60),
                    )

                    if response.status == 200:
                        image_data = await response.read()

                        # Determine extension
                        ext = filename.split(".")[-1] if "." in filename else "png"

                        # Upload to blob storage if configured
                        if self.blob_storage.is_enabled:
                            blob_url = self.blob_storage.upload_bytes(
                                image_data, extension=ext
                            )
                            print(f"Uploaded ComfyUI image to blob storage: {blob_url}")
                            return blob_url

                        # Otherwise save locally
                        image_path = os.path.join(
                            output_directory, f"{uuid.uuid4()}.{ext}"
                        )

                        with open(image_path, "wb") as f:
                            f.write(image_data)

                        print(f"Downloaded image from ComfyUI: {image_path}")
                        return image_path
                    else:
                        raise Exception(f"Failed to download image: {response.status}")

        raise Exception("No images found in ComfyUI outputs")
