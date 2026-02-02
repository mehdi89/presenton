"""
Azure Blob Storage service for persistent image storage.

When AZURE_STORAGE_CONNECTION_STRING is set, images are uploaded to Azure Blob Storage
and public URLs are returned. Otherwise, falls back to local file storage.
"""

import uuid
from typing import Optional
from azure.storage.blob import BlobServiceClient, ContainerClient, ContentSettings
from utils.get_env import (
    get_azure_storage_connection_string_env,
    get_azure_storage_container_env,
    get_azure_storage_exports_container_env,
)


class BlobStorageService:
    """Service for uploading files to Azure Blob Storage."""

    def __init__(self):
        self.connection_string = get_azure_storage_connection_string_env()
        self.container_name = get_azure_storage_container_env()
        self.exports_container_name = get_azure_storage_exports_container_env()
        self._client: Optional[BlobServiceClient] = None
        self._container_client = None
        self._exports_container_client: Optional[ContainerClient] = None

    @property
    def is_enabled(self) -> bool:
        """Check if Azure Blob Storage is configured."""
        return bool(self.connection_string)

    def _get_client(self) -> BlobServiceClient:
        """Lazy initialization of blob service client."""
        if self._client is None:
            self._client = BlobServiceClient.from_connection_string(
                self.connection_string
            )
        return self._client

    def _get_container_client(self):
        """Get container client, creating container if needed."""
        if self._container_client is None:
            client = self._get_client()
            self._container_client = client.get_container_client(self.container_name)
            # Ensure container exists
            try:
                self._container_client.get_container_properties()
            except Exception:
                self._container_client.create_container(public_access="blob")
        return self._container_client

    def _get_exports_container_client(self) -> ContainerClient:
        """Get exports container client, creating container if needed."""
        if self._exports_container_client is None:
            client = self._get_client()
            self._exports_container_client = client.get_container_client(
                self.exports_container_name
            )
            # Ensure container exists
            try:
                self._exports_container_client.get_container_properties()
            except Exception:
                self._exports_container_client.create_container(public_access="blob")
        return self._exports_container_client

    def upload_export(self, file_path: str) -> str:
        """
        Upload an export file (PDF/PPTX) to the exports container.

        Args:
            file_path: Path to the file on disk

        Returns:
            Public URL to the uploaded blob
        """
        import os

        if not self.is_enabled:
            raise RuntimeError("Azure Blob Storage is not configured")

        filename = os.path.basename(file_path)
        extension = os.path.splitext(file_path)[1].lstrip(".")

        # Content type mapping
        content_types = {
            "pdf": "application/pdf",
            "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        }
        content_type = content_types.get(extension.lower(), "application/octet-stream")

        # Upload to exports container
        container_client = self._get_exports_container_client()
        blob_client = container_client.get_blob_client(filename)

        with open(file_path, "rb") as f:
            blob_client.upload_blob(
                f.read(),
                overwrite=True,
                content_settings=ContentSettings(
                    content_type=content_type,
                    content_disposition=f'attachment; filename="{filename}"',
                ),
            )

        return blob_client.url

    def upload_bytes(
        self,
        data: bytes,
        extension: str = "png",
        content_type: Optional[str] = None,
        filename: Optional[str] = None,
    ) -> str:
        """
        Upload bytes to blob storage and return the public URL.

        Args:
            data: The file content as bytes
            extension: File extension (e.g., 'png', 'jpg')
            content_type: MIME type (auto-detected if not provided)
            filename: Optional filename to preserve (for exports)

        Returns:
            Public URL to the uploaded blob
        """
        if not self.is_enabled:
            raise RuntimeError("Azure Blob Storage is not configured")

        # Use provided filename or generate unique blob name
        if filename:
            blob_name = filename
        else:
            blob_name = f"{uuid.uuid4()}.{extension}"

        # Auto-detect content type if not provided
        if content_type is None:
            content_types = {
                "png": "image/png",
                "jpg": "image/jpeg",
                "jpeg": "image/jpeg",
                "gif": "image/gif",
                "webp": "image/webp",
                "pdf": "application/pdf",
                "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            }
            content_type = content_types.get(extension.lower(), "application/octet-stream")

        # Upload to blob storage
        container_client = self._get_container_client()
        blob_client = container_client.get_blob_client(blob_name)

        blob_client.upload_blob(
            data,
            overwrite=True,
            content_settings=ContentSettings(content_type=content_type),
        )

        # Return public URL
        return blob_client.url

    def upload_file(self, file_path: str, preserve_filename: bool = True) -> str:
        """
        Upload a file from disk to blob storage and return the public URL.

        Args:
            file_path: Path to the file on disk
            preserve_filename: If True, use the original filename in blob storage

        Returns:
            Public URL to the uploaded blob
        """
        import os

        extension = os.path.splitext(file_path)[1].lstrip(".")
        filename = os.path.basename(file_path) if preserve_filename else None
        with open(file_path, "rb") as f:
            return self.upload_bytes(f.read(), extension=extension, filename=filename)

    def delete_blob(self, blob_url: str) -> bool:
        """
        Delete a blob by its URL.

        Args:
            blob_url: The public URL of the blob

        Returns:
            True if deleted, False if not found or error
        """
        if not self.is_enabled:
            return False

        try:
            # Extract blob name from URL
            # URL format: https://<account>.blob.core.windows.net/<container>/<blob_name>
            blob_name = blob_url.split(f"/{self.container_name}/")[-1]
            container_client = self._get_container_client()
            blob_client = container_client.get_blob_client(blob_name)
            blob_client.delete_blob()
            return True
        except Exception as e:
            print(f"Failed to delete blob: {e}")
            return False


# Singleton instance
_blob_storage_service: Optional[BlobStorageService] = None


def get_blob_storage_service() -> BlobStorageService:
    """Get the singleton blob storage service instance."""
    global _blob_storage_service
    if _blob_storage_service is None:
        _blob_storage_service = BlobStorageService()
    return _blob_storage_service
