import path from "path";
import fs from "fs";
import puppeteer, { Browser } from "puppeteer";

import { sanitizeFilename } from "@/app/(presentation-generator)/utils/others";
import { NextResponse, NextRequest } from "next/server";
import { uploadToBlob, isBlobStorageEnabled } from "@/lib/blob-storage";

export async function POST(req: NextRequest) {
  let browser: Browser | null = null;

  try {
    const { id, title } = await req.json();
    if (!id) {
      return NextResponse.json(
        { error: "Missing Presentation ID" },
        { status: 400 }
      );
    }

    // Check environment variable early before doing expensive operations
    const appDataDirectory = process.env.APP_DATA_DIRECTORY;
    if (!appDataDirectory) {
      console.error("[PDF Export] APP_DATA_DIRECTORY environment variable not set");
      return NextResponse.json(
        { error: "App data directory not configured. Please set APP_DATA_DIRECTORY environment variable." },
        { status: 500 }
      );
    }

    // Launch browser with error handling
    try {
      browser = await puppeteer.launch({
        executablePath: process.env.PUPPETEER_EXECUTABLE_PATH,
        headless: true,
        args: [
          "--no-sandbox",
          "--disable-setuid-sandbox",
          "--disable-dev-shm-usage",
          "--disable-gpu",
          "--disable-web-security",
          "--disable-background-timer-throttling",
          "--disable-backgrounding-occluded-windows",
          "--disable-renderer-backgrounding",
          "--disable-features=TranslateUI",
          "--disable-ipc-flooding-protection",
        ],
      });
    } catch (launchError) {
      console.error("[PDF Export] Failed to launch browser:", launchError);
      return NextResponse.json(
        { error: "Failed to launch PDF renderer. Please check Puppeteer configuration." },
        { status: 500 }
      );
    }

    const page = await browser.newPage();
    await page.setViewport({ width: 1280, height: 720 });
    page.setDefaultNavigationTimeout(300000);
    page.setDefaultTimeout(300000);

    // Navigate to the PDF maker page
    try {
      await page.goto(`http://localhost/pdf-maker?id=${id}`, {
        waitUntil: "networkidle0",
        timeout: 300000,
      });
    } catch (navError) {
      console.error("[PDF Export] Failed to navigate to PDF maker page:", navError);
      await browser.close();
      return NextResponse.json(
        { error: "Failed to load presentation for PDF export. Please try again." },
        { status: 500 }
      );
    }

    await page.waitForFunction('() => document.readyState === "complete"');

    try {
      await page.waitForFunction(
        `
        () => {
          const allElements = document.querySelectorAll('*');
          let loadedElements = 0;
          let totalElements = allElements.length;

          for (let el of allElements) {
              const style = window.getComputedStyle(el);
              const isVisible = style.display !== 'none' &&
                              style.visibility !== 'hidden' &&
                              style.opacity !== '0';

              if (isVisible && el.offsetWidth > 0 && el.offsetHeight > 0) {
                  loadedElements++;
              }
          }

          return (loadedElements / totalElements) >= 0.99;
        }
        `,
        { timeout: 300000 }
      );

      await new Promise((resolve) => setTimeout(resolve, 1000));
    } catch (error) {
      console.log("[PDF Export] Warning: Some content may not have loaded completely:", error);
    }

    const pdfBuffer = await page.pdf({
      width: "1280px",
      height: "720px",
      printBackground: true,
      margin: { top: 0, right: 0, bottom: 0, left: 0 },
    });

    await browser.close();
    browser = null;

    const sanitizedTitle = sanitizeFilename(title ?? "presentation");
    const filename = `${sanitizedTitle}_${Date.now()}.pdf`;

    // Try to upload to Azure Blob Storage first (for multi-replica support)
    if (isBlobStorageEnabled()) {
      const blobUrl = await uploadToBlob(
        Buffer.from(pdfBuffer),
        filename,
        "application/pdf"
      );
      if (blobUrl) {
        console.log(`[PDF Export] Uploaded to blob storage: ${blobUrl}`);
        return NextResponse.json({
          success: true,
          path: blobUrl,
        });
      }
      console.log("[PDF Export] Blob upload failed, falling back to local storage");
    }

    // Fallback to local filesystem (for local development)
    const destinationPath = path.join(
      appDataDirectory,
      "exports",
      filename
    );
    await fs.promises.mkdir(path.dirname(destinationPath), { recursive: true });
    await fs.promises.writeFile(destinationPath, pdfBuffer);

    // Return download URL with URL-encoded filename
    const downloadUrl = `/api/download/${encodeURIComponent(filename)}`;

    return NextResponse.json({
      success: true,
      path: downloadUrl,
    });
  } catch (error) {
    console.error("[PDF Export] Unexpected error:", error);
    return NextResponse.json(
      { error: "Failed to export PDF. Please try again." },
      { status: 500 }
    );
  } finally {
    // Ensure browser is closed even on error
    if (browser) {
      try {
        await browser.close();
      } catch (closeError) {
        console.error("[PDF Export] Error closing browser:", closeError);
      }
    }
  }
}
