import type { Metadata } from "next";
import { IBM_Plex_Mono, Manrope } from "next/font/google";

import { Providers } from "@/app/providers";
import "./globals.css";

const heading = Manrope({ subsets: ["latin"], variable: "--font-sans" });
const mono = IBM_Plex_Mono({ subsets: ["latin"], variable: "--font-mono", weight: ["400", "500"] });

export const metadata: Metadata = {
  title: "AegisCore",
  description: "AI-assisted defensive SOC platform for alerts, incidents, telemetry, and explainable prioritization.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${heading.variable} ${mono.variable}`}>
      <body className="font-[var(--font-sans)] antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
