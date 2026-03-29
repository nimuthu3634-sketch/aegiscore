import Image from "next/image";
import Link from "next/link";

import { appConfig } from "@/lib/config";
import { cn } from "@/lib/utils";

export function Logo({
  href,
  compact = false,
  className,
}: {
  href?: string;
  compact?: boolean;
  className?: string;
}) {
  const content = (
    <div className={cn("flex items-center gap-3", className)}>
      <div className={cn("relative overflow-hidden rounded-2xl bg-white", compact ? "h-10 w-10 p-1.5" : "h-14 w-14 p-2")}>
        <Image alt={`${appConfig.appName} logo`} fill priority sizes="56px" src="/aegiscore-logo.svg" className="object-contain p-1.5" />
      </div>
      {!compact ? (
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-[#8f8f8f]">AegisCore</p>
          <p className="mt-1 text-base font-semibold text-[#111111]">Defensive SOC Platform</p>
        </div>
      ) : null}
    </div>
  );

  if (!href) {
    return content;
  }

  return <Link href={href}>{content}</Link>;
}
