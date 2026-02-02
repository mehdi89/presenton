/**
 * Azure Blob Storage service for persistent export storage.
 *
 * When AZURE_STORAGE_CONNECTION_STRING is set, exports (PDF/PPTX) are uploaded
 * to Azure Blob Storage and public URLs are returned. This enables multi-replica
 * support in Azure Container Apps.
 */

import { BlobServiceClient, ContainerClient } from "@azure/storage-blob";

const EXPORTS_CONTAINER = process.env.AZURE_STORAGE_EXPORTS_CONTAINER || "exports";

let blobServiceClient: BlobServiceClient | null = null;
let containerClient: ContainerClient | null = null;

function getConnectionString(): string | undefined {
  return process.env.AZURE_STORAGE_CONNECTION_STRING;
}

function getBlobServiceClient(): BlobServiceClient | null {
  if (blobServiceClient) return blobServiceClient;

  const connectionString = getConnectionString();
  if (!connectionString) {
    return null;
  }

  blobServiceClient = BlobServiceClient.fromConnectionString(connectionString);
  return blobServiceClient;
}

async function getContainerClient(): Promise<ContainerClient | null> {
  if (containerClient) return containerClient;

  const client = getBlobServiceClient();
  if (!client) return null;

  containerClient = client.getContainerClient(EXPORTS_CONTAINER);

  // Ensure container exists with public blob access
  try {
    await containerClient.createIfNotExists({
      access: "blob", // Public read access for blobs
    });
  } catch (error) {
    console.error("[BlobStorage] Failed to create container:", error);
    // Container might already exist, continue
  }

  return containerClient;
}

/**
 * Check if Azure Blob Storage is configured
 */
export function isBlobStorageEnabled(): boolean {
  return !!getConnectionString();
}

/**
 * Upload a buffer to Azure Blob Storage
 *
 * @param data - File content as Buffer
 * @param filename - The filename to use for the blob
 * @param contentType - MIME type of the file
 * @returns Public URL to the uploaded blob, or null if blob storage is not configured
 */
export async function uploadToBlob(
  data: Buffer,
  filename: string,
  contentType: string
): Promise<string | null> {
  const container = await getContainerClient();
  if (!container) {
    console.log("[BlobStorage] Not configured, skipping upload");
    return null;
  }

  try {
    const blobClient = container.getBlockBlobClient(filename);

    // Encode filename for Content-Disposition header (handle Unicode)
    const safeFilename = filename.replace(/[^\x20-\x7E]/g, "_");
    const encodedFilename = encodeURIComponent(filename);

    await blobClient.uploadData(data, {
      blobHTTPHeaders: {
        blobContentType: contentType,
        // RFC 5987: filename for ASCII, filename* for UTF-8
        blobContentDisposition: `attachment; filename="${safeFilename}"; filename*=UTF-8''${encodedFilename}`,
      },
    });

    console.log(`[BlobStorage] Uploaded: ${blobClient.url}`);
    return blobClient.url;
  } catch (error) {
    console.error("[BlobStorage] Upload failed:", error);
    return null;
  }
}

/**
 * Delete a blob by filename
 */
export async function deleteBlob(filename: string): Promise<boolean> {
  const container = await getContainerClient();
  if (!container) return false;

  try {
    const blobClient = container.getBlockBlobClient(filename);
    await blobClient.deleteIfExists();
    return true;
  } catch (error) {
    console.error("[BlobStorage] Delete failed:", error);
    return false;
  }
}
