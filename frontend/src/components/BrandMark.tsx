import fullLogoUrl from "@repo-assets/aegiscore-logo.svg";

import { classNames } from "@/utils/classNames";

type BrandMarkSize = "xs" | "sm" | "md" | "lg" | "xl";
type BrandMarkTone = "light" | "dark";

type BrandMarkProps = {
  size?: BrandMarkSize;
  tone?: BrandMarkTone;
  alt?: string;
  className?: string;
};

const sizeClasses: Record<BrandMarkSize, string> = {
  xs: "h-10 w-32 rounded-[1rem] px-2.5 py-2",
  sm: "h-12 w-40 rounded-[1.15rem] px-3 py-2.5",
  md: "h-14 w-44 rounded-[1.35rem] px-3.5 py-3",
  lg: "h-[4.5rem] w-[14rem] rounded-[1.6rem] px-4 py-3.5",
  xl: "h-[5rem] w-[16.5rem] rounded-[1.8rem] px-4 py-4 sm:h-[5.5rem] sm:w-[18rem] sm:rounded-[2rem]",
};

const toneClasses: Record<BrandMarkTone, string> = {
  light: "border border-brand-black/8 bg-white/90 ring-1 ring-brand-orange/10 shadow-soft",
  dark: "border border-brand-white/12 bg-white/95 ring-1 ring-brand-orange/10 shadow-float backdrop-blur-sm",
};

export function BrandMark({
  size = "md",
  tone = "light",
  alt = "AegisCore logo",
  className,
}: BrandMarkProps) {
  return (
    <div
      className={classNames(
        "flex shrink-0 items-center justify-center overflow-hidden",
        sizeClasses[size],
        toneClasses[tone],
        className,
      )}
    >
      <img src={fullLogoUrl} alt={alt} className="h-full w-full object-contain" />
    </div>
  );
}
