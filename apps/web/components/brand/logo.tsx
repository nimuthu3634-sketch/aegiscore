import Image from "next/image";
import Link from "next/link";

import { appConfig } from "@/lib/config";
import { cn } from "@/lib/utils";

export function Logo({
  href,
  compact = false,
  size = "default",
  className,
  tone = "dark",
}: {
  href?: string;
  compact?: boolean;
  size?: "default" | "large";
  className?: string;
  tone?: "dark" | "light";
}) {
  const lightTone = tone === "light";
  const iconSizeClass = compact ? "h-11 w-11 p-1.5" : size === "large" ? "h-20 w-20 p-2.5" : "h-16 w-16 p-2";
  const imageSize = compact ? "44px" : size === "large" ? "80px" : "64px";
  const content = (
    <div className={cn("flex items-center gap-3", className)}>
      <div
        className={cn(
          "relative overflow-hidden rounded-[22px] border",
          iconSizeClass,
          lightTone
            ? "border-white/10 bg-white/95 shadow-[0_16px_30px_rgba(0,0,0,0.18)]"
            : "border-black/8 bg-white shadow-[0_18px_32px_rgba(17,17,17,0.08)]",
        )}
      >
        <Image alt={`${appConfig.appName} logo`} fill priority sizes={imageSize} src="/aegiscore-logo.svg" className="object-contain p-1.5" />
      </div>
      {!compact ? (
        <div>
          <p className={cn(size === "large" ? "text-xs tracking-[0.34em]" : "text-[11px] tracking-[0.32em]", "uppercase", lightTone ? "text-white/45" : "text-[#8f8f8f]")}>
            AegisCore
          </p>
          <p className={cn(size === "large" ? "mt-1.5 text-xl" : "mt-1 text-base", "font-semibold tracking-[-0.03em]", lightTone ? "text-white" : "text-[#111111]")}>
            Defensive SOC Platform
          </p>
        </div>
      ) : null}
    </div>
  );

  if (!href) {
    return content;
  }

  return <Link href={href}>{content}</Link>;
}
