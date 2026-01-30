import { useCallback } from "react";
import { useRouter, useSearchParams } from "next/navigation";

export const usePresentationNavigation = (
  presentationId: string,
  selectedSlide: number,
  setSelectedSlide: (slide: number) => void,
  setIsFullscreen: (fullscreen: boolean) => void
) => {
  const router = useRouter();
  const searchParams = useSearchParams();

  const isPresentMode = searchParams.get("mode") === "present";
  const stream = searchParams.get("stream");
  const returnUrl = searchParams.get("returnUrl");
  const summaryId = searchParams.get("summaryId");
  const currentSlide = parseInt(
    searchParams.get("slide") || `${selectedSlide}` || "0"
  );

  // Helper to build URL with preserved params
  const buildUrl = useCallback((basePath: string, additionalParams: Record<string, string> = {}) => {
    let url = `${basePath}?id=${presentationId}`;

    // Add additional params first
    Object.entries(additionalParams).forEach(([key, value]) => {
      url += `&${key}=${encodeURIComponent(value)}`;
    });

    // Preserve returnUrl and summaryId
    if (returnUrl) {
      url += `&returnUrl=${encodeURIComponent(returnUrl)}`;
    }
    if (summaryId) {
      url += `&summaryId=${encodeURIComponent(summaryId)}`;
    }

    return url;
  }, [presentationId, returnUrl, summaryId]);

  const handleSlideClick = useCallback((index: number) => {
    const slideElement = document.getElementById(`slide-${index}`);
    if (slideElement) {
      slideElement.scrollIntoView({
        behavior: "smooth",
        block: "center",
      });
      setSelectedSlide(index);
    }
  }, [setSelectedSlide]);

  const toggleFullscreen = useCallback(() => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen();
      setIsFullscreen(true);
    } else {
      document.exitFullscreen();
      setIsFullscreen(false);
    }
  }, [setIsFullscreen]);

  const handlePresentExit = useCallback(() => {
    setIsFullscreen(false);
    router.push(buildUrl('/presentation'));
  }, [router, buildUrl, setIsFullscreen]);

  const handleSlideChange = useCallback((newSlide: number, presentationData: any) => {
    if (newSlide >= 0 && newSlide < presentationData?.slides.length!) {
      setSelectedSlide(newSlide);
      router.push(
        buildUrl('/presentation', { mode: 'present', slide: newSlide.toString() }),
        { scroll: false }
      );
    }
  }, [router, buildUrl, setSelectedSlide]);

  return {
    isPresentMode,
    stream,
    returnUrl,
    summaryId,
    currentSlide,
    handleSlideClick,
    toggleFullscreen,
    handlePresentExit,
    handleSlideChange,
  };
}; 