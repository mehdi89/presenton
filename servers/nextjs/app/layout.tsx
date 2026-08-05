import type { Metadata } from "next";
import localFont from "next/font/local";
import { Manrope, Syne, Unbounded } from "next/font/google";
import "./globals.css";
import "katex/dist/katex.min.css";
import { Providers } from "./providers";
import MixpanelInitializer from "./MixpanelInitializer";
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

const syne = Syne({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800"],
  variable: "--font-syne",
});

const manrope = Manrope({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800"],
  variable: "--font-manrope",
});

const unbounded = Unbounded({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800"],
  variable: "--font-unbounded",
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
      <head>
        <link rel="preload" href="/Presenton_Splash.png" as="image" />
      </head>
      <body
        className={`${inter.variable} ${syne.variable} ${manrope.variable} ${unbounded.variable} antialiased`}
      >
        <Providers>
          <MixpanelInitializer>
            <RouteRestriction>
              {children}
            </RouteRestriction>
          </MixpanelInitializer>
        </Providers>
        <Toaster position="top-center" />
        <script
          dangerouslySetInnerHTML={{
            __html: `
              window.addEventListener('error', function(e) {
                if (e.message && (e.message.includes('Loading chunk') || e.message.includes('ChunkLoadError'))) {
                  if (!sessionStorage.getItem('chunk-reload')) {
                    sessionStorage.setItem('chunk-reload', '1');
                    window.location.reload();
                  }
                }
              });
            `,
          }}
        />
      </body>
    </html>
  );
}
