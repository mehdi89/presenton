"use client";
import { Button } from "@/components/ui/button";
import {
  Download,
  Play,
  Loader2,
  Redo2,
  Undo2,
  ArrowLeft,
} from "lucide-react";
import React, { useState } from "react";
import Wrapper from "@/components/Wrapper";
import { useRouter, usePathname } from "next/navigation";
import { PresentationGenerationApi } from "../../services/api/presentation-generation";
import { OverlayLoader } from "@/components/ui/overlay-loader";
import { useDispatch, useSelector } from "react-redux";

import { RootState } from "@/store/store";
import { toast } from "sonner";


import Announcement from "@/components/Announcement";
import { PptxPresentationModel } from "@/types/pptx_models";
import { trackEvent, MixpanelEvent } from "@/utils/mixpanel";
import { usePresentationUndoRedo } from "../hooks/PresentationUndoRedo";
import ToolTip from "@/components/ToolTip";

const Header = ({
  presentation_id,
  currentSlide,
  returnUrl,
  summaryId,
}: {
  presentation_id: string;
  currentSlide?: number;
  returnUrl?: string;
  summaryId?: string;
}) => {
  const [showLoader, setShowLoader] = useState(false);
  const router = useRouter();
  const pathname = usePathname();
  const dispatch = useDispatch();


  const { presentationData, isStreaming } = useSelector(
    (state: RootState) => state.presentationGeneration
  );

  const { onUndo, onRedo, canUndo, canRedo } = usePresentationUndoRedo();

  const get_presentation_pptx_model = async (id: string): Promise<PptxPresentationModel> => {
    const response = await fetch(`/api/presentation_to_pptx_model?id=${id}`);
    const pptx_model = await response.json();
    return pptx_model;
  };

  const handleExportPptx = async () => {
    if (isStreaming) return;

    try {
      setShowLoader(true);
      // Save the presentation data before exporting
      trackEvent(MixpanelEvent.Header_UpdatePresentationContent_API_Call);
      await PresentationGenerationApi.updatePresentationContent(presentationData);
      trackEvent(MixpanelEvent.Header_GetPptxModel_API_Call);
      const pptx_model = await get_presentation_pptx_model(presentation_id);
      if (!pptx_model) {
        throw new Error("Failed to get presentation PPTX model");
      }
      trackEvent(MixpanelEvent.Header_ExportAsPPTX_API_Call);
      const pptx_path = await PresentationGenerationApi.exportAsPPTX(pptx_model);
      if (pptx_path) {
        // window.open(pptx_path, '_self');
        downloadLink(pptx_path);
      } else {
        throw new Error("No path returned from export");
      }
    } catch (error) {
      console.error("Export failed:", error);
      setShowLoader(false);
      toast.error("Having trouble exporting!", {
        description:
          "We are having trouble exporting your presentation. Please try again.",
      });
    } finally {
      setShowLoader(false);
    }
  };

  const handleExportPdf = async () => {
    if (isStreaming) return;

    try {
      setShowLoader(true);
      // Save the presentation data before exporting
      trackEvent(MixpanelEvent.Header_UpdatePresentationContent_API_Call);
      await PresentationGenerationApi.updatePresentationContent(presentationData);

      trackEvent(MixpanelEvent.Header_ExportAsPDF_API_Call);
      const response = await fetch('/api/export-as-pdf', {
        method: 'POST',
        body: JSON.stringify({
          id: presentation_id,
          title: presentationData?.title,
        })
      });

      if (response.ok) {
        const { path: pdfPath } = await response.json();
        // window.open(pdfPath, '_blank');
        downloadLink(pdfPath);
      } else {
        throw new Error("Failed to export PDF");
      }

    } catch (err) {
      console.error(err);
      toast.error("Having trouble exporting!", {
        description:
          "We are having trouble exporting your presentation. Please try again.",
      });
    } finally {
      setShowLoader(false);
    }
  };
  const downloadLink = (downloadPath: string) => {
    // Use a hidden iframe to trigger the download
    // This bypasses popup blockers and works in async contexts
    // because iframes with Content-Disposition: attachment trigger downloads
    const iframe = document.createElement('iframe');
    iframe.style.display = 'none';
    iframe.src = downloadPath;
    document.body.appendChild(iframe);

    // Clean up after download starts (give it time to initiate)
    setTimeout(() => {
      if (iframe.parentNode) {
        iframe.parentNode.removeChild(iframe);
      }
    }, 10000); // 10 seconds to allow large file downloads to start
  };

  const MenuItems = ({ mobile }: { mobile: boolean }) => (
    <div className="flex items-center gap-2 lg:gap-4">
      {/* undo redo */}
      <div className="flex items-center gap-1 lg:gap-2">
        <ToolTip content="Undo">
          <button disabled={!canUndo} className="text-gray-700 disabled:opacity-50 hover:text-[#2299DD]" onClick={() => {
            onUndo();
          }}>

            <Undo2 className="w-6 h-6 " />

          </button>
        </ToolTip>
        <ToolTip content="Redo">

          <button disabled={!canRedo} className="text-gray-700 disabled:opacity-50 hover:text-[#2299DD]" onClick={() => {
            onRedo();
          }}>
            <Redo2 className="w-6 h-6 " />

          </button>
        </ToolTip>

      </div>

      {/* Present Button */}
      <Button
        onClick={() => {
          const to = `?id=${presentation_id}&mode=present&slide=${currentSlide || 0}`;
          trackEvent(MixpanelEvent.Navigation, { from: pathname, to });
          router.push(to);
        }}
        variant="ghost"
        className="border border-gray-300 font-bold text-gray-700 rounded-[32px] transition-all duration-300 hover:bg-gray-100 group"
      >
        <Play className="w-4 h-4 mr-1" />
        Present
      </Button>

      {/* PDF Export Button */}
      <ToolTip content="Export as PDF">
        <Button
          onClick={() => {
            trackEvent(MixpanelEvent.Header_Export_PDF_Button_Clicked, { pathname });
            handleExportPdf();
          }}
          variant="ghost"
          className="border border-gray-300 font-bold text-gray-700 rounded-[32px] transition-all duration-300 hover:bg-[#2299DD] hover:text-white hover:border-[#2299DD]"
        >
          <Download className="w-4 h-4 mr-1" />
          <span className="hidden sm:inline">PDF</span>
        </Button>
      </ToolTip>

      {/* PPTX Export Button */}
      <ToolTip content="Export as PPTX">
        <Button
          onClick={() => {
            trackEvent(MixpanelEvent.Header_Export_PPTX_Button_Clicked, { pathname });
            handleExportPptx();
          }}
          variant="ghost"
          className="border border-gray-300 font-bold text-gray-700 rounded-[32px] transition-all duration-300 hover:bg-[#2299DD] hover:text-white hover:border-[#2299DD]"
        >
          <Download className="w-4 h-4 mr-1" />
          <span className="hidden sm:inline">PPTX</span>
        </Button>
      </ToolTip>
    </div>
  );

  return (
    <>
      <OverlayLoader
        show={showLoader}
        text="Exporting presentation..."
        showProgress={true}
        duration={40}
      />
      <div
        className="bg-white w-full shadow-lg sticky top-0 border-b border-gray-200 z-50">

        <Announcement />
        <Wrapper className="flex items-center justify-between py-3">
          <div className="flex items-center gap-3">
            <ToolTip content={returnUrl && summaryId ? "Back to Summaries" : "Back to Dashboard"}>
              <button
                onClick={() => {
                  if (returnUrl && summaryId) {
                    const redirectUrl = `${returnUrl}/summaries/${summaryId}`;
                    trackEvent(MixpanelEvent.Navigation, { from: pathname, to: redirectUrl });
                    // If in iframe, break out to parent; otherwise normal navigation
                    if (window.self !== window.top) {
                      window.top!.location.href = redirectUrl;
                    } else {
                      window.location.href = redirectUrl;
                    }
                  } else {
                    trackEvent(MixpanelEvent.Navigation, { from: pathname, to: '/dashboard' });
                    router.push('/dashboard');
                  }
                }}
                className="text-gray-700 hover:text-[#2299DD] transition-colors"
              >
                <ArrowLeft className="w-6 h-6" />
              </button>
            </ToolTip>
            <div className="h-6 w-px bg-gray-300" />
            <span className="text-xl font-semibold text-gray-800">Presenton</span>
          </div>

          {/* Desktop Menu */}
          <div className="hidden lg:flex items-center gap-4 2xl:gap-6">
            {isStreaming && (
              <Loader2 className="animate-spin text-[#2299DD] font-bold w-6 h-6" />
            )}


            <MenuItems mobile={false} />
          </div>

          {/* Mobile Menu */}
          <div className="lg:hidden flex items-center gap-4">
            <MenuItems mobile={true} />
          </div>
        </Wrapper>

      </div>
    </>
  );
};

export default Header;
