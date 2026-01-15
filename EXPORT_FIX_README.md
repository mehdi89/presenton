# Export Functionality Fix

This document explains the fixes applied to resolve export issues in Presenton.

## Issues Fixed

### 1. Export Popover Not Showing
**Problem**: When clicking the Export button, the dropdown menu with PDF/PPTX options wasn't visible.

**Root Cause**: The Popover component uses a Portal (renders outside the DOM hierarchy), but the z-index styling was applied to the wrapper div instead of the PopoverContent itself.

**Fix Applied**:
- Removed inline `style={{zIndex: 100}}` from wrapper div in `servers/nextjs/app/(presentation-generator)/presentation/components/Header.tsx`
- Added `z-[9999]` className directly to `PopoverContent` component (line 223)

### 2. Export Functionality Not Working
**Problem**: Export endpoints were failing because the FastAPI backend wasn't running.

**Root Causes**:
1. FastAPI backend server (port 8000) was not started
2. Next.js app wasn't properly configured to proxy API requests to FastAPI
3. Missing environment variables for export directories

**Fixes Applied**:

#### a. Added API Proxy Configuration
Updated `servers/nextjs/next.config.mjs` to proxy `/api/v1/*` requests to FastAPI backend at `http://localhost:8000`.

#### b. Created Environment Variables
Created `servers/nextjs/.env.local` with required variables:
- `TEMP_DIRECTORY`: For screenshots and temporary files
- `APP_DATA_DIRECTORY`: For exported presentations
- `PUPPETEER_EXECUTABLE_PATH`: For Chromium (optional, uses bundled version if empty)

#### c. Created App Data Directories
Created necessary directories:
```
app_data/
├── temp/      # Temporary files and screenshots
├── exports/   # Exported PPTX and PDF files
└── fonts/     # Custom fonts
```

#### d. Created FastAPI Startup Script
Created `start-fastapi.sh` to easily start the FastAPI backend server.

## How to Use

### Quick Start

1. **Start the FastAPI Backend** (in a new terminal):
   ```bash
   cd /Users/macbookm2air/Desktop/tubeOnAI/presenton
   ./start-fastapi.sh
   ```

   Or manually:
   ```bash
   cd servers/fastapi
   uv sync  # First time only
   uv run uvicorn api.main:app --host 0.0.0.0 --port 8000
   ```

2. **Start the Next.js Frontend** (if not already running):
   ```bash
   cd servers/nextjs
   npm run dev
   ```

3. **Access Presenton**:
   - Open http://localhost:3000 in your browser
   - The export functionality should now work!

### Verifying the Fix

1. **Check Export Popover**:
   - Click the "Export" button in the header
   - You should see a dropdown with "Export as PDF" and "Export as PPTX" options

2. **Test Export Functionality**:
   - Create a presentation
   - Click "Export" → "Export as PPTX" or "Export as PDF"
   - The presentation should be exported to `app_data/exports/`

### Troubleshooting

#### "Export options not showing"
- Hard refresh your browser (Cmd+Shift+R on Mac, Ctrl+Shift+R on Windows)
- Clear browser cache
- Check browser console for errors (F12)

#### "Export failed" error
1. **Check if FastAPI is running**:
   ```bash
   curl http://localhost:8000/api/v1/ppt/presentation/export/pptx
   ```
   Should return a 422 error (expected - means server is running)

2. **Check environment variables**:
   ```bash
   cd servers/nextjs
   cat .env.local
   ```
   Should show TEMP_DIRECTORY and APP_DATA_DIRECTORY

3. **Check directories exist**:
   ```bash
   ls -la app_data/temp app_data/exports
   ```

4. **Check logs**:
   - FastAPI logs in the terminal where you ran `start-fastapi.sh`
   - Next.js logs in the terminal where you ran `npm run dev`
   - Browser console (F12 → Console tab)

#### Puppeteer errors
If you see Chromium-related errors:

**Option 1**: Install Chromium via Puppeteer
```bash
cd servers/nextjs
npx puppeteer install chrome
```

**Option 2**: Use system Chrome/Chromium
Add to `.env.local`:
```
PUPPETEER_EXECUTABLE_PATH=/Applications/Google Chrome.app/Contents/MacOS/Google Chrome
```
(Adjust path for your system)

## Technical Details

### Export Flow

1. **User clicks "Export as PPTX"**:
   - Header.tsx → `handleExportPptx()`
   - Saves presentation data via `/api/v1/ppt/presentation/update`
   - Gets PPTX model via `/api/presentation_to_pptx_model?id={id}`
   - Exports PPTX via `/api/v1/ppt/presentation/export/pptx`

2. **User clicks "Export as PDF"**:
   - Header.tsx → `handleExportPdf()`
   - Saves presentation data via `/api/v1/ppt/presentation/update`
   - Exports PDF via `/api/export-as-pdf`

### `/api/presentation_to_pptx_model` Endpoint
- Uses Puppeteer to navigate to `/pdf-maker?id={id}`
- Captures slide elements and their styles
- Converts to PPTX-compatible format
- Requires TEMP_DIRECTORY for screenshots

### `/api/export-as-pdf` Endpoint
- Uses Puppeteer to navigate to `/pdf-maker?id={id}`
- Generates PDF from rendered slides
- Saves to APP_DATA_DIRECTORY/exports

## Files Modified

1. `servers/nextjs/app/(presentation-generator)/presentation/components/Header.tsx`
   - Fixed Popover z-index issue

2. `servers/nextjs/next.config.mjs`
   - Added API proxy rewrites

3. `servers/nextjs/.env.local` (created)
   - Added environment variables

4. `start-fastapi.sh` (created)
   - FastAPI startup script

5. `app_data/` directories (created)
   - temp/, exports/, fonts/

## Notes

- The FastAPI backend must be running for export to work
- Export files are saved to `app_data/exports/`
- Temporary files during export are in `app_data/temp/`
- The Next.js dev server must be restarted after modifying `.env.local`

## Support

If issues persist:
1. Check all logs (FastAPI, Next.js, Browser console)
2. Verify all services are running on correct ports
3. Ensure all environment variables are set
4. Check file permissions on app_data directories
