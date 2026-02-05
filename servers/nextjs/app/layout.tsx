import type { Metadata } from "next";
import localFont from "next/font/local";
import { Roboto, Instrument_Sans } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";
import MixpanelInitializer from "./MixpanelInitializer";
import { LayoutProvider } from "./(presentation-generator)/context/LayoutContext";
import { Toaster } from "@/components/ui/sonner";
import RouteRestriction from "@/components/RouteRestriction";
const inter = localFont({
  src: [
    {
      path: "./fonts/Inter.ttf",
      weight: "400",
      style: "normal",
    },
  ],
  variable: "--font-inter",
});

const instrument_sans = Instrument_Sans({
  subsets: ["latin"],
  weight: ["400"],
  variable: "--font-instrument-sans",
});

const roboto = Roboto({
  subsets: ["latin"],
  weight: ["400"],
  variable: "--font-roboto",
});


export const metadata: Metadata = {
  metadataBase: new URL("https://slides.tubeonai.com"),
  title: "TubeOnAI - AI Presentation Generator",
  description:
    "AI-powered presentation generator with custom layouts, multi-model support, and PDF/PPTX export.",
  keywords: [
    "AI presentation generator",
    "data storytelling",
    "data visualization tool",
    "AI data presentation",
    "presentation generator",
    "data to presentation",
    "interactive presentations",
    "professional slides",
  ],
  openGraph: {
    title: "TubeOnAI - AI Presentation Generator",
    description:
      "AI-powered presentation generator with custom layouts, multi-model support, and PDF/PPTX export.",
    url: "https://slides.tubeonai.com",
    siteName: "TubeOnAI",
    type: "website",
    locale: "en_US",
  },
  alternates: {
    canonical: "https://slides.tubeonai.com",
  },
  twitter: {
    card: "summary_large_image",
    title: "TubeOnAI - AI Presentation Generator",
    description:
      "AI-powered presentation generator with custom layouts, multi-model support, and PDF/PPTX export.",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {

  return (
    <html lang="en">
      <body
        className={`${inter.variable} ${roboto.variable} ${instrument_sans.variable} antialiased`}
      >
        <Providers>
          <MixpanelInitializer>
            <LayoutProvider>
              <RouteRestriction>
                {children}
              </RouteRestriction>
            </LayoutProvider>
          </MixpanelInitializer>
        </Providers>
        <Toaster position="top-center" />
      </body>
    </html>
  );
}
