'use client'
import React, { useEffect, useState } from "react";
import PresentationPage from "./components/PresentationPage";
import PresentationSetupPage from "./components/PresentationSetupPage";
import { Button } from "@/components/ui/button";
import { useRouter, useSearchParams } from "next/navigation";
import { DashboardApi } from "../services/api/dashboard";
import { Loader2 } from "lucide-react";

const page = () => {
  const router = useRouter();
  const params = useSearchParams();
  const queryId = params.get("id");
  const returnUrl = params.get("returnUrl");
  const summaryId = params.get("summaryId");
  const mode = params.get("mode"); // "setup" | "present" | null
  const stream = params.get("stream"); // "true" when slides are being generated

  // If mode is explicit or stream=true (slides being generated), skip auto-detection
  const skipDetection = !!mode || stream === "true";

  // Auto-detect setup mode when no explicit mode or stream param
  const [detectedMode, setDetectedMode] = useState<"setup" | "present" | null>(
    mode as "setup" | "present" | null
  );
  const [detecting, setDetecting] = useState(!skipDetection && !!queryId);

  useEffect(() => {
    if (skipDetection || !queryId) {
      // Update detectedMode when mode param changes (e.g., after redirect)
      if (mode) {
        setDetectedMode(mode as "setup" | "present");
      } else if (stream === "true") {
        setDetectedMode("present");
      }
      setDetecting(false);
      return;
    }

    setDetecting(true);
    let cancelled = false;
    DashboardApi.getPresentation(queryId)
      .then((data) => {
        if (cancelled) return;
        const hasSlides = data?.slides && data.slides.length > 0;
        setDetectedMode(hasSlides ? "present" : "setup");
      })
      .catch(() => {
        if (cancelled) return;
        // On error, fall through to presentation page
        setDetectedMode("present");
      })
      .finally(() => {
        if (!cancelled) setDetecting(false);
      });

    return () => { cancelled = true; };
  }, [mode, queryId, skipDetection, stream]);

  if (!queryId) {
    return (
      <div className="flex flex-col items-center justify-center h-screen font-syne">
        <h1 className="text-2xl font-bold">No presentation id found</h1>
        <p className="text-gray-500 pb-4">Please try again</p>
        <Button onClick={() => router.push("/dashboard")}>Go to home</Button>
      </div>
    );
  }

  // Show loading while auto-detecting mode
  if (detecting) {
    return (
      <div className="flex flex-col items-center justify-center h-screen gap-4">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
        <p className="text-gray-500">Loading presentation...</p>
      </div>
    );
  }

  // Setup mode: Show template selection and outline editing before generation
  if (detectedMode === "setup") {
    return (
      <PresentationSetupPage
        presentation_id={queryId}
        returnUrl={returnUrl || undefined}
        summaryId={summaryId || undefined}
      />
    );
  }

  // Default: Show the presentation view/edit page
  return (
    <PresentationPage
      presentation_id={queryId}
      returnUrl={returnUrl || undefined}
      summaryId={summaryId || undefined}
    />
  );
};

export default page;
