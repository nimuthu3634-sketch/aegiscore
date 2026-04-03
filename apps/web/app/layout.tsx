import type { Metadata } from "next";

import { Providers } from "@/app/providers";
import { brandName } from "@aegiscore/config";
import "./globals.css";

export const metadata: Metadata = {
  title: brandName,
  description: "AI-assisted defensive SOC platform for alerts, incidents, telemetry, and explainable prioritization.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="font-[var(--font-sans)] antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
