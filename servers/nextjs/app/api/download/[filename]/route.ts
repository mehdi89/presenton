import { NextRequest, NextResponse } from "next/server";
import fs from "fs";
import path from "path";

export async function GET(
  request: NextRequest,
  { params }: { params: { filename: string } }
) {
  try {
    const { filename } = params;

    // Prevent directory traversal attacks
    if (filename.includes("..") || filename.includes("/") || filename.includes("\\")) {
      return NextResponse.json(
        { error: "Invalid filename" },
        { status: 400 }
      );
    }

    const appDataDirectory = process.env.APP_DATA_DIRECTORY;
    if (!appDataDirectory) {
      return NextResponse.json(
        { error: "App data directory not configured" },
        { status: 500 }
      );
    }

    const filePath = path.join(appDataDirectory, "exports", filename);

    // Check if file exists
    if (!fs.existsSync(filePath)) {
      return NextResponse.json(
        { error: "File not found" },
        { status: 404 }
      );
    }

    // Read the file
    const fileBuffer = await fs.promises.readFile(filePath);

    // Determine content type based on file extension
    const ext = path.extname(filename).toLowerCase();
    const contentType = ext === ".pdf"
      ? "application/pdf"
      : ext === ".pptx"
      ? "application/vnd.openxmlformats-officedocument.presentationml.presentation"
      : "application/octet-stream";

    // Return file with appropriate headers for download
    return new NextResponse(fileBuffer, {
      headers: {
        "Content-Type": contentType,
        "Content-Disposition": `attachment; filename="${filename}"`,
        "Content-Length": fileBuffer.length.toString(),
      },
    });
  } catch (error) {
    console.error("Download error:", error);
    return NextResponse.json(
      { error: "Failed to download file" },
      { status: 500 }
    );
  }
}
