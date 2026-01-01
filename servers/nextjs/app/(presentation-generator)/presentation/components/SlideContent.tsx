import React, { useEffect, useState, useMemo } from "react";
import { Loader2, PlusIcon, Trash2, StickyNote } from "lucide-react";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { toast } from "sonner";
import ToolTip from "@/components/ToolTip";
import { RootState } from "@/store/store";
import { useDispatch, useSelector } from "react-redux";
import {
  deletePresentationSlide,
} from "@/store/slices/presentationGeneration";
import { useTemplateLayouts } from "../../hooks/useTemplateLayouts";
import { usePathname } from "next/navigation";
import { trackEvent, MixpanelEvent } from "@/utils/mixpanel";
import NewSlide from "../../components/NewSlide";
import { addToHistory } from "@/store/slices/undoRedoSlice";

interface SlideContentProps {
  slide: any;
  index: number;
  presentationId: string;
}

const SlideContent = ({ slide, index, presentationId }: SlideContentProps) => {
  const dispatch = useDispatch();
  const [showNewSlideSelection, setShowNewSlideSelection] = useState(false);
  const { presentationData, isStreaming } = useSelector(
    (state: RootState) => state.presentationGeneration
  );

  // Use the centralized group layouts hook
  const { renderSlideContent, loading } = useTemplateLayouts();
  const pathname = usePathname();
  const onDeleteSlide = async () => {
    try {
      trackEvent(MixpanelEvent.Slide_Delete_API_Call);
      // Add current state to past
      dispatch(addToHistory({
        slides: presentationData?.slides,
        actionType: "DELETE_SLIDE"
      }));
      dispatch(deletePresentationSlide(slide.index));

    } catch (error: any) {
      console.error("Error deleting slide:", error);
      toast.error("Error deleting slide.", {
        description: error.message || "Error deleting slide.",
      });
    }
  };
  // Scroll to the new slide when streaming and new slides are being generated
  useEffect(() => {
    if (
      presentationData &&
      presentationData?.slides &&
      presentationData.slides.length > 1 &&
      isStreaming
    ) {
      // Scroll to the last slide (newly generated during streaming)
      const lastSlideIndex = presentationData.slides.length - 1;
      const slideElement = document.getElementById(
        `slide-${presentationData.slides[lastSlideIndex].index}`
      );
      if (slideElement) {
        slideElement.scrollIntoView({
          behavior: "smooth",
          block: "center",
        });
      }
    }
  }, [presentationData?.slides?.length, isStreaming]);

  // Memoized slide content rendering to prevent unnecessary re-renders
  const slideContent = useMemo(() => {
    return renderSlideContent(slide, isStreaming ? false : true); // Enable edit mode for main content
  }, [renderSlideContent, slide, isStreaming]);

  useEffect(() => {
    if (loading) {
      return;
    }
    if (slide.layout.includes("custom")) {

      const existingScript = document.querySelector(
        'script[src*="tailwindcss.com"]'
      );
      if (!existingScript) {
        const script = document.createElement("script");
        script.src = "https://cdn.tailwindcss.com";
        script.async = true;
        document.head.appendChild(script);
      }
    }
  }, [slide, isStreaming, loading]);

  return (
    <>
      <div
        id={`slide-${slide.index}`}
        className=" w-full max-w-[1280px] main-slide flex items-center max-md:mb-4 justify-center relative"
      >
        {isStreaming && (
          <Loader2 className="w-8 h-8 absolute right-2 top-2 z-30 text-blue-800 animate-spin" />
        )}
        <div
          data-layout={slide.layout}
          data-group={slide.layout_group}
          className={` w-full  group `}
        >
          {/* render slides */}
          {loading ? (
            <div className="flex flex-col bg-white aspect-video items-center justify-center h-full">
              <Loader2 className="w-8 h-8 animate-spin" />
            </div>
          ) : (
            slideContent
          )}

          {!showNewSlideSelection && (
            <div className="group-hover:opacity-100 hidden md:block opacity-0 transition-opacity my-4 duration-300">
              <ToolTip content="Add new slide below">
                {!isStreaming && !loading && (
                  <div
                    onClick={() => {
                      trackEvent(MixpanelEvent.Slide_Add_New_Slide_Button_Clicked, { pathname });
                      setShowNewSlideSelection(true);
                    }}
                    className="  bg-white shadow-md w-[80px] py-2 border hover:border-[#2299DD] duration-300  flex items-center justify-center rounded-lg cursor-pointer mx-auto"
                  >
                    <PlusIcon className="text-gray-500 text-base cursor-pointer" />
                  </div>
                )}
              </ToolTip>
            </div>
          )}
          {showNewSlideSelection && !loading && (
            <NewSlide
              index={index}
              templateID={`${slide.layout.split(":")[0]}`}
              setShowNewSlideSelection={setShowNewSlideSelection}
              presentationId={presentationId}
            />
          )}

          {!isStreaming && !loading && (
            <ToolTip content="Delete slide">
              <div
                onClick={() => {
                  trackEvent(MixpanelEvent.Slide_Delete_Slide_Button_Clicked, { pathname });
                  onDeleteSlide();
                }}
                className="absolute top-2 z-20 sm:top-4 right-2 sm:right-4 hidden md:block  transition-transform"
              >
                <Trash2 className="text-gray-500 text-xl cursor-pointer" />
              </div>
            </ToolTip>
          )}
          {/* Speaker Notes */}
          {!isStreaming && slide?.speaker_note && (
            <div className="absolute top-2 z-20 sm:top-4 right-8 sm:right-12 hidden md:block transition-transform">
              <Popover>
                <PopoverTrigger asChild>
                  <div className=" cursor-pointer ">
                    <ToolTip content="Show speaker notes">
                      <StickyNote className="text-xl text-gray-500" />
                    </ToolTip>
                  </div>
                </PopoverTrigger>
                <PopoverContent side="left" align="start" sideOffset={10} className="w-[320px] z-30">
                  <div className="space-y-2">
                    <p className="text-xs font-semibold text-gray-600">Speaker notes</p>
                    <div className="text-sm text-gray-800 whitespace-pre-wrap max-h-64 overflow-auto">
                      {slide.speaker_note}
                    </div>
                  </div>
                </PopoverContent>
              </Popover>
            </div>
          )}
        </div>
      </div>
    </>
  );
};

export default SlideContent;
