'use client'
import React from "react";
import PresentationPage from "./components/PresentationPage";
import PresentationSetupPage from "./components/PresentationSetupPage";
import { Button } from "@/components/ui/button";
import { useRouter, useSearchParams } from "next/navigation";

const page = () => {
  const router = useRouter();
  const params = useSearchParams();
  const queryId = params.get("id");
  const returnUrl = params.get("returnUrl");
  const summaryId = params.get("summaryId");
  const mode = params.get("mode"); // "setup" | "present" | null

  if (!queryId) {
    return (
      <div className="flex flex-col items-center justify-center h-screen">
        <h1 className="text-2xl font-bold">No presentation id found</h1>
        <p className="text-gray-500 pb-4">Please try again</p>
        <Button onClick={() => router.push("/dashboard")}>Go to home</Button>
      </div>
    );
  }

  // Setup mode: Show template selection and outline editing before generation
  if (mode === "setup") {
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
