import Image from "next/image";
import Link from "next/link";

import { appConfig } from "@/lib/config";
import { cn } from "@/lib/utils";

export function Logo({
  href,
  compact = false,
  className,
  tone = "dark",
}: {
  href?: string;
  compact?: boolean;
  className?: string;
  tone?: "dark" | "light";
}) {
  const lightTone = tone === "light";
  const content = (
    <div className={cn("flex items-center gap-3", className)}>
      <div
        className={cn(
          "relative overflow-hidden rounded-[22px] border",
          compact ? "h-10 w-10 p-1.5" : "h-14 w-14 p-2",
          lightTone
            ? "border-white/10 bg-white/95 shadow-[0_16px_30px_rgba(0,0,0,0.18)]"
            : "border-black/8 bg-white shadow-[0_18px_32px_rgba(17,17,17,0.08)]",
        )}
      >
        <Image alt={`${appConfig.appName} logo`} fill priority sizes="56px" src="/aegiscore-logo.svg" className="object-contain p-1.5" />
      </div>
      {!compact ? (
        <div>
          <p className={cn("text-[11px] uppercase tracking-[0.32em]", lightTone ? "text-white/45" : "text-[#8f8f8f]")}>AegisCore</p>
          <p className={cn("mt-1 text-base font-semibold tracking-[-0.03em]", lightTone ? "text-white" : "text-[#111111]")}>
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
