import logoUrl from "@repo-assets/aegiscore-logo.svg";

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
  xs: "h-10 w-10 rounded-[1rem] p-2",
  sm: "h-12 w-12 rounded-[1.15rem] p-2.5",
  md: "h-14 w-14 rounded-[1.35rem] p-3",
  lg: "h-[4.5rem] w-[4.5rem] rounded-[1.6rem] p-3.5",
  xl: "h-[5rem] w-[5rem] rounded-[1.8rem] p-4 sm:h-[5.5rem] sm:w-[5.5rem] sm:rounded-[2rem]",
};

const toneClasses: Record<BrandMarkTone, string> = {
  light: "border border-brand-black/8 bg-white/90 ring-1 ring-brand-orange/10 shadow-soft",
  dark: "border border-brand-white/12 bg-white/10 ring-1 ring-white/5 shadow-float backdrop-blur-sm",
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
      <img src={logoUrl} alt={alt} className="h-full w-full object-contain" />
    </div>
  );
}
