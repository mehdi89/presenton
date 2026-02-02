/**
 * Azure Blob Storage service for persistent export storage.
 *
 * When AZURE_STORAGE_CONNECTION_STRING is set, exports (PDF/PPTX) are uploaded
 * to Azure Blob Storage and public URLs are returned. This enables multi-replica
 * support in Azure Container Apps.
 *
 * Uses dynamic imports to avoid crypto/digest errors in Next.js when blob storage
 * is not configured.
 */

const EXPORTS_CONTAINER = process.env.AZURE_STORAGE_EXPORTS_CONTAINER || "exports";

function getConnectionString(): string | undefined {
  return process.env.AZURE_STORAGE_CONNECTION_STRING;
}

/**
 * Check if Azure Blob Storage is configured
 */
export function isBlobStorageEnabled(): boolean {
  const connStr = getConnectionString();
  return !!connStr && connStr.trim().length > 0;
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
  if (!isBlobStorageEnabled()) {
    console.log("[BlobStorage] Not configured, skipping upload");
    return null;
  }

  try {
    // Dynamic import to avoid crypto errors when not using blob storage
    const { BlobServiceClient } = await import("@azure/storage-blob");

    const connectionString = getConnectionString()!;
    const blobServiceClient = BlobServiceClient.fromConnectionString(connectionString);
    const containerClient = blobServiceClient.getContainerClient(EXPORTS_CONTAINER);

    // Ensure container exists with public blob access
    try {
      await containerClient.createIfNotExists({
        access: "blob",
      });
    } catch (error) {
      // Container might already exist, continue
      console.log("[BlobStorage] Container check:", error);
    }

    const blobClient = containerClient.getBlockBlobClient(filename);

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
  if (!isBlobStorageEnabled()) return false;

  try {
    const { BlobServiceClient } = await import("@azure/storage-blob");

    const connectionString = getConnectionString()!;
    const blobServiceClient = BlobServiceClient.fromConnectionString(connectionString);
    const containerClient = blobServiceClient.getContainerClient(EXPORTS_CONTAINER);
    const blobClient = containerClient.getBlockBlobClient(filename);

    await blobClient.deleteIfExists();
    return true;
  } catch (error) {
    console.error("[BlobStorage] Delete failed:", error);
    return false;
  }
}
