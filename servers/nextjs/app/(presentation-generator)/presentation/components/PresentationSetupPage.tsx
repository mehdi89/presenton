"use client";

import React, { useState, useEffect } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { RootState } from "@/store/store";
import { useSelector, useDispatch } from "react-redux";
import { OverlayLoader } from "@/components/ui/overlay-loader";
import Wrapper from "@/components/Wrapper";
import { useRouter } from "next/navigation";
import { ArrowLeft, Loader2, Sparkles } from "lucide-react";
import { toast } from "sonner";

import OutlineContent from "../../outline/components/OutlineContent";
import TemplateSelection from "../../outline/components/TemplateSelection";
import { Template } from "../../outline/types/index";
import TemplateService from "../../services/api/template";
import { useOutlineManagement } from "../../outline/hooks/useOutlineManagement";
import { PresentationGenerationApi } from "../../services/api/presentation-generation";
import {
  setOutlines,
  setPresentationId,
  setStreaming,
  clearOutlines,
} from "@/store/slices/presentationGeneration";
import ToolTip from "@/components/ToolTip";

const TABS = {
  OUTLINE: "outline",
  TEMPLATE: "template",
};

interface PresentationSetupPageProps {
  presentation_id: string;
  returnUrl?: string;
  summaryId?: string;
}

const PresentationSetupPage: React.FC<PresentationSetupPageProps> = ({
  presentation_id,
  returnUrl,
  summaryId,
}) => {
  const router = useRouter();
  const dispatch = useDispatch();

  const { outlines } = useSelector(
    (state: RootState) => state.presentationGeneration
  );

  const [activeTab, setActiveTab] = useState<string>(TABS.OUTLINE);
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const [loadingMessage, setLoadingMessage] = useState("Loading presentation...");
  const [error, setError] = useState<string | null>(null);

  // Use the outline management hook for drag/drop and add functionality
  const { handleDragEnd, handleAddSlide } = useOutlineManagement(outlines);

  // Fetch presentation data on mount
  useEffect(() => {
    const fetchPresentationData = async () => {
      try {
        setIsLoading(true);
        setError(null);

        const response = await fetch(`/api/v1/ppt/presentation/${presentation_id}`);
        if (!response.ok) {
          throw new Error("Failed to fetch presentation");
        }

        const data = await response.json();

        // Set the presentation ID in Redux
        dispatch(setPresentationId(presentation_id));

        // Extract outlines from the presentation data
        if (data.outlines?.slides && data.outlines.slides.length > 0) {
          dispatch(setOutlines(data.outlines.slides));
          setIsLoading(false);
        } else if (data.slides && data.slides.length > 0) {
          // If slides exist, extract content as outlines
          const extractedOutlines = data.slides.map((slide: any) => ({
            content: slide.content?.title || slide.content?.heading || "Slide content",
          }));
          dispatch(setOutlines(extractedOutlines));
          setIsLoading(false);
        } else {
          // No outlines exist yet - need to generate them via streaming
          console.log("[PresentationSetupPage] No outlines found, starting generation...");
          setLoadingMessage("Generating outlines...");
          await generateOutlinesFromStream();
        }
      } catch (err: any) {
        console.error("Error fetching presentation:", err);
        setError(err.message || "Failed to load presentation");
        setIsLoading(false);
      }
    };

    // Stream outlines from the server
    const generateOutlinesFromStream = async () => {
      try {
        dispatch(setStreaming(true));

        const response = await fetch(`/api/v1/ppt/outlines/stream/${presentation_id}`, {
          method: "GET",
          headers: {
            Accept: "text/event-stream",
          },
        });

        if (!response.ok) {
          throw new Error(`Failed to stream outlines: ${response.status}`);
        }

        const reader = response.body?.getReader();
        if (!reader) {
          throw new Error("No reader available");
        }

        const decoder = new TextDecoder();
        let collectedOutlines: { content: string }[] = [];

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value, { stream: true });
          const lines = chunk.split("\n");

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              try {
                const jsonData = JSON.parse(line.slice(6));

                if (jsonData.type === "status") {
                  setLoadingMessage(jsonData.status);
                } else if (jsonData.type === "complete" && jsonData.presentation) {
                  // Extract outlines from complete response
                  if (jsonData.presentation.outlines?.slides) {
                    collectedOutlines = jsonData.presentation.outlines.slides;
                  }
                } else if (jsonData.type === "error") {
                  throw new Error(jsonData.detail || "Outline generation failed");
                }
              } catch (parseError) {
                // Ignore JSON parse errors for incomplete chunks
              }
            }
          }
        }

        // Set the outlines in Redux
        if (collectedOutlines.length > 0) {
          dispatch(setOutlines(collectedOutlines));
        }

        dispatch(setStreaming(false));
        setIsLoading(false);
      } catch (err: any) {
        console.error("Error streaming outlines:", err);
        dispatch(setStreaming(false));
        setError(err.message || "Failed to generate outlines");
        setIsLoading(false);
      }
    };

    fetchPresentationData();

    // Cleanup on unmount
    return () => {
      dispatch(clearOutlines());
    };
  }, [presentation_id, dispatch]);

  // Handle generate button click
  const handleGenerate = async () => {
    if (!selectedTemplate) {
      toast.error("Please select a template first");
      setActiveTab(TABS.TEMPLATE);
      return;
    }

    if (!selectedTemplate.slides || selectedTemplate.slides.length === 0) {
      toast.error("Invalid template - no slide layouts found");
      setActiveTab(TABS.TEMPLATE);
      return;
    }

    if (outlines.length === 0) {
      toast.error("No outlines available for generation");
      return;
    }

    try {
      setIsGenerating(true);
      setLoadingMessage("Preparing presentation...");

      // Prepare layout data from selected template
      const layoutData = {
        name: selectedTemplate.name,
        ordered: selectedTemplate.ordered,
        slides: selectedTemplate.slides,
      };

      console.log("[PresentationSetupPage] Preparing with layout:", {
        name: layoutData.name,
        ordered: layoutData.ordered,
        slidesCount: layoutData.slides?.length,
      });

      // Call prepare endpoint with selected template and outlines
      await PresentationGenerationApi.presentationPrepare({
        presentation_id,
        outlines: outlines,
        layout: layoutData,
        title: null, // Let backend use existing title
      });

      setLoadingMessage("Redirecting to presentation...");

      // Build redirect URL with query params
      // IMPORTANT: Include stream=true to trigger slide generation streaming
      let redirectUrl = `/presentation?id=${presentation_id}&stream=true`;
      if (returnUrl) {
        redirectUrl += `&returnUrl=${encodeURIComponent(returnUrl)}`;
      }
      if (summaryId) {
        redirectUrl += `&summaryId=${encodeURIComponent(summaryId)}`;
      }

      // Redirect to the presentation page (which will start streaming)
      router.push(redirectUrl);
    } catch (err: any) {
      console.error("Error generating presentation:", err);
      toast.error(err.message || "Failed to generate presentation");
      setIsGenerating(false);
    }
  };

  const handleSelectTemplate = async (template: {
    id: string;
    name: string;
    source: "default" | "custom";
    position: number;
  }) => {
    try {
      const fullTemplate = await TemplateService.getTemplateDetails(template.id);
      setSelectedTemplate(fullTemplate as unknown as Template);
    } catch (error) {
      toast.error("Failed to load template details");
    }
  };

  // Handle back button
  const handleBack = () => {
    // Extract domain from returnUrl and redirect to main page
    let redirectUrl = 'https://web.tubeonai.com';
    if (returnUrl) {
      try {
        const url = new URL(returnUrl);
        redirectUrl = url.origin;
      } catch {
        // If URL parsing fails, use default
      }
    }
    // Previous logic - redirect to full summaries path:
    // if (returnUrl && summaryId) {
    //   const redirectUrl = `${returnUrl}/summaries/${summaryId}`;
    //   if (window.self !== window.top) {
    //     window.top!.location.href = redirectUrl;
    //   } else {
    //     window.location.href = redirectUrl;
    //   }
    // } else {
    //   router.push("/dashboard");
    // }
    if (window.self !== window.top) {
      window.top!.location.href = redirectUrl;
    } else {
      window.location.href = redirectUrl;
    }
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-screen bg-gray-50">
        <Loader2 className="w-12 h-12 animate-spin text-[#2299DD] mb-4" />
        <p className="text-gray-600">{loadingMessage}</p>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-screen bg-gray-50">
        <div className="text-center">
          <h2 className="text-xl font-semibold text-gray-800 mb-2">
            Failed to load presentation
          </h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <Button onClick={() => router.push("/dashboard")}>Go to Dashboard</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      <OverlayLoader
        show={isGenerating}
        text={loadingMessage}
        showProgress={true}
        duration={60}
      />

      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-50">
        <Wrapper className="flex items-center justify-between py-3">
          <div className="flex items-center gap-3">
            <ToolTip content="Back">
              <button
                onClick={handleBack}
                className="text-gray-700 hover:text-[#2299DD] transition-colors"
              >
                <ArrowLeft className="w-6 h-6" />
              </button>
            </ToolTip>
            <div className="h-6 w-px bg-gray-300" />
            <img src="/tubeonai-logo.svg" alt="TubeOnAI" className="h-7" />
          </div>
          <div className="text-sm text-gray-500">
            Setup your presentation
          </div>
        </Wrapper>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-hidden">
        <Wrapper className="h-full flex flex-col py-4">
          <div className="flex-grow overflow-y-hidden max-w-[1200px] w-full mx-auto">
            <Tabs value={activeTab} onValueChange={setActiveTab} className="h-full flex flex-col">
              <TabsList className="grid w-full max-w-md mx-auto mb-4 grid-cols-2">
                <TabsTrigger value={TABS.OUTLINE}>
                  1. Review Outline
                </TabsTrigger>
                <TabsTrigger value={TABS.TEMPLATE}>
                  2. Select Template
                </TabsTrigger>
              </TabsList>

              <div className="flex-grow overflow-hidden">
                <TabsContent
                  value={TABS.OUTLINE}
                  className="h-[calc(100vh-16rem)] overflow-y-auto custom_scrollbar"
                >
                  <div className="pb-4">
                    <div className="text-center mb-6">
                      <h2 className="text-xl font-semibold text-gray-800">
                        Review and Edit Your Outline
                      </h2>
                      <p className="text-gray-600 text-sm mt-1">
                        Drag to reorder slides, edit content, or add new slides
                      </p>
                    </div>
                    <OutlineContent
                      outlines={outlines}
                      isLoading={false}
                      isStreaming={false}
                      statusMessage=""
                      activeSlideIndex={-1}
                      highestActiveIndex={outlines.length - 1}
                      onDragEnd={handleDragEnd}
                      onAddSlide={handleAddSlide}
                    />
                  </div>
                </TabsContent>

                <TabsContent
                  value={TABS.TEMPLATE}
                  className="h-[calc(100vh-16rem)] overflow-y-auto custom_scrollbar"
                >
                  <div className="pb-4">
                    <div className="text-center mb-6">
                      <h2 className="text-xl font-semibold text-gray-800">
                        Choose a Template
                      </h2>
                      <p className="text-gray-600 text-sm mt-1">
                        Select a template that best fits your presentation style
                      </p>
                    </div>
                    <TemplateSelection
                      presentationId={presentation_id}
                      selectedTemplateId={selectedTemplate?.id ?? null}
                      onSelectTemplate={handleSelectTemplate}
                    />
                  </div>
                </TabsContent>
              </div>
            </Tabs>
          </div>

          {/* Generate Button */}
          <div className="py-4 border-t border-gray-200 bg-white mt-auto">
            <div className="max-w-[1200px] mx-auto flex items-center justify-between">
              <div className="text-sm text-gray-600">
                {outlines.length} slides • {selectedTemplate ? selectedTemplate.name : "No template selected"}
              </div>
              <Button
                onClick={handleGenerate}
                disabled={isGenerating || outlines.length === 0}
                className="bg-[#2299DD] hover:bg-[#1a7bb8] text-white px-6 py-2 rounded-full flex items-center gap-2"
              >
                {isGenerating ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4" />
                    Generate Presentation
                  </>
                )}
              </Button>
            </div>
          </div>
        </Wrapper>
      </div>
    </div>
  );
};

export default PresentationSetupPage;
